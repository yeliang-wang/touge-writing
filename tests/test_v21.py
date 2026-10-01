"""Observable v2.1 behavior, using only synthetic temporary works."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from workspace_lib import write_json, digest, immutable_copy
from writing_workspace import init_project, set_chapters, add_revision, context, validate, derive_state
from material_index import normalize, search, read_source, attest_read, register_mapping, relations
from capability_catalog import catalog, resolve, ROOT
import writing_run as runs


class V21Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.project = init_project(self.root/'workspace', 'synthetic', '合成作品', 'novel')
        set_chapters(self.project, [{'id':'scene-a','title':'第一场'}, {'id':'scene-b','title':'第二场'}])
        self.source = self.project/'source.md'; self.source.write_text('合成来源：空表导入显示成功，没有实际数据。\n')
        self.request = {'schema_version':1,'id':'run-1','task':'按现有材料试写独立片段',
                        'authorization_refs':['synthetic-task-1'], 'target':'scene-b','mode':'trial','stage':'draft',
                        'fiction_policy':{'mode':'source-based'}, 'capabilities':['scene-design@1.0.0'],
                        'inputs':[{'path':'source.md','sha256':digest(self.source),'summary':'空表失败事件'}],
                        'open_issues':[]}

    def start(self): return runs.start(self.project, self.request)
    def text(self):
        self.start(); return runs.add_artifact(self.project,'run-1','save-1',self.source,'draft-1')
    def corpus(self, fmt='json'):
        d=self.root/'corpus'; d.mkdir(exist_ok=True); (d/'a.md').write_text('港岸工具在演示中导入空表。\n'); (d/'b.md').write_text('另一篇谈排班。\n')
        rows=[{'id':'a','markdown':'a.md','word_count':15,'title':'旧章名','aliases':['河岸软件'],'tags':['演示']},
              {'id':'b','markdown':'b.md','word_count':8,'title':'排班'}]
        p=d/('manifest.'+fmt)
        if fmt=='jsonl':
            rows=[{'id':r['id'],'source_id':'same-collection','text_path':r['markdown'],
                   'text_hash':hashlib.sha256((d/r['markdown']).read_text()[:-1].encode()).hexdigest(),
                   'title':r['title'],'aliases':r.get('aliases',[])} for r in rows]
            p.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
        else: write_json(p,rows)
        return p

    def test_catalog_explicit_version_and_scope(self):
        self.assertEqual(len(catalog()['capabilities']),13)
        self.assertEqual(resolve(['scene-design@1.0.0'],'novel')[0]['version'],'1.0.0')
        for specs in [['scene-design'],['scene-design@99.0.0'],['scene-design@1.0.0']*2]:
            with self.assertRaises(ValueError):resolve(specs)

    def test_both_manifest_formats_and_document_identity(self):
        for fmt in ['json','jsonl']:
            p=self.corpus(fmt); before=digest(p); rows=normalize(p)
            self.assertEqual({r['source_id'] for r in rows},{'a','b'})
            self.assertEqual(search(p,'河岸软件')[0]['source_id'],'a')
            self.assertFalse(rows[0]['facts_verified']); self.assertEqual(digest(p),before)

    def test_source_hash_and_scope_rejected(self):
        p=self.corpus('jsonl'); (p.parent/'a.md').write_text('被改过\n')
        with self.assertRaises(ValueError):normalize(p)
        p=self.corpus(); rows=json.loads(p.read_text());rows[0]['markdown']='../outside.md';write_json(p,rows)
        with self.assertRaises(ValueError):normalize(p)

    def test_search_and_delivery_are_not_read_or_fact_confirmation(self):
        p=self.corpus(); hit=search(p,'空表')[0];self.assertEqual(hit['read_state'],'search_hit')
        delivery=read_source(p,'a');self.assertTrue(delivery['full_text_delivered']);self.assertIn('空表',delivery['content'])
        with self.assertRaises(ValueError):attest_read(self.project,'read-1',delivery,'','')
        receipt=attest_read(self.project,'read-1',delivery,'host:read:1','已读空表导入事件')
        self.assertEqual(receipt['read_state'],'host_attested');self.assertFalse(receipt['facts_verified'])
        changed=dict(delivery,content='伪造阅读内容')
        with self.assertRaises(ValueError):attest_read(self.project,'read-2',changed,'host:2','summary')

    def test_mapping_many_to_many_without_relabeling_chapters(self):
        p=self.corpus(); source=normalize(p)[0]
        data={'schema_version':1,'id':'map-1','sources':[{'key':'a-v1','manifest':str(p),'source_id':'a','sha256':source['sha256']}],
              'units':[{'id':'event-1','label':'旧表第三章的演示事件','status':'supported',
                        'anchors':[{'source_key':'a-v1','start_line':1,'end_line':1,'quote':'导入空表'}]}],
              'usages':[{'unit_id':'event-1','chapter_id':'scene-a','role':'main_scene'}, {'unit_id':'event-1','chapter_id':'scene-b','role':'echo'}]}
        before=digest(self.project/'book.yaml');register_mapping(self.project,data);register_mapping(self.project,data)
        self.assertEqual(digest(self.project/'book.yaml'),before)
        found=relations(self.project,'map-1',chapter_id='scene-b')
        self.assertEqual([r['role'] for r in found['usages']],['echo'])
        self.assertEqual(found['sources'][0]['source_id'],'a')
        altered=copy.deepcopy(data);altered['usages'][0]['chapter_id']='ch03'
        with self.assertRaises(ValueError):register_mapping(self.project,altered)
        altered=copy.deepcopy(data);altered['id']='map-2';altered['units'][0]['anchors'][0]['quote']='不存在'
        with self.assertRaises(ValueError):register_mapping(self.project,altered)

    def test_active_task_overrides_legacy_next_chapter_and_pins_actual_content(self):
        self.assertEqual(context(self.project)['selected_chapter'],'scene-a')
        r=self.start();self.assertEqual(context(self.project)['selected_chapter'],'scene-b')
        self.assertEqual(context(self.project,'scene-a')['selected_chapter'],'scene-a')
        source=next(p for p in r['run']['pins'] if p['source']=='source.md')
        self.assertEqual(source['summary_basis_sha256'],digest(self.source))
        self.assertIn('book.yaml',[p['source'] for p in r['run']['pins']])
        self.assertEqual(r['run']['model']['id'],'unknown')

    def test_start_retry_and_prepared_without_event(self):
        with patch('writing_run.append_event',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.start()
        self.start();self.start();self.assertEqual(len(runs.events(self.project)),1)
        changed=dict(self.request,task='changed')
        with self.assertRaises(ValueError):runs.start(self.project,changed)

    def test_input_drift_and_snapshot_tampering(self):
        self.start();self.source.write_text('changed');r=runs.verify(self.project,'run-1')
        self.assertTrue(any(d['label']=='source.md' for d in r['drift']))
        pin=next(p for p in r['run']['pins'] if p['source']=='source.md')
        (runs.paths(self.project,'run-1')/pin['snapshot']).write_text('changed snapshot')
        with self.assertRaises(ValueError):runs.verify(self.project,'run-1')

    def test_public_definition_drift_keeps_pinned_version(self):
        self.start()
        alternate=self.root/'empty-package';alternate.mkdir()
        checked=runs.verify(self.project,'run-1',alternate)
        self.assertTrue(any(d['origin']=='public' for d in checked['drift']))
        self.assertTrue(all(d['snapshot_usable'] for d in checked['drift']))

    def test_artifact_copy_before_event_recovers_once(self):
        self.start()
        with patch('writing_run.append_event',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):runs.add_artifact(self.project,'run-1','save-1',self.source,'draft-1')
        runs.add_artifact(self.project,'run-1','save-1',self.source,'draft-1')
        runs.add_artifact(self.project,'run-1','save-1',self.source,'draft-1')
        self.assertEqual(len(runs.derive(self.project)['runs']['run-1']['artifacts']),1)
        self.source.write_text('different')
        with self.assertRaises(ValueError):runs.add_artifact(self.project,'run-1','save-1',self.source,'draft-1')

    def test_registration_after_content_commit_recovers_missing_event(self):
        self.text();revision={'revision_id':'scene-b-draft-1','kind':'text','version':'0.1','status':'draft','chapter_id':'scene-b'}
        with patch('writing_run.append_event',side_effect=RuntimeError('crash')):
            with self.assertRaises(RuntimeError):runs.register(self.project,'run-1','register-1','draft-1',revision)
        self.assertEqual(len(json.loads((self.project/'版本记录/revisions.json').read_text())['revisions']),1)
        runs.register(self.project,'run-1','register-1','draft-1',revision)
        runs.register(self.project,'run-1','register-1','draft-1',revision)
        self.assertEqual(runs.derive(self.project)['runs']['run-1']['registered_versions'],['scene-b-draft-1'])
        with self.assertRaises(ValueError):runs.register(self.project,'run-1','register-1','draft-1',dict(revision,version='different'))

    def test_cross_chapter_registration_and_fake_acceptance_refused(self):
        self.text()
        with self.assertRaises(ValueError):runs.register(self.project,'run-1','reg','draft-1',{'revision_id':'wrong','kind':'text','version':'1','status':'draft','chapter_id':'scene-a'})
        with self.assertRaises(ValueError):runs.register(self.project,'run-1','reg','draft-1',{'revision_id':'false','kind':'text','version':'1','status':'accepted','chapter_id':'scene-b'})

    def finish(self):
        text=self.text()['payload']['artifact']
        runs.change_stage(self.project,'run-1','to-review','review','阅读正文')
        review=self.project/'review.json';write_json(review,{'scope':'合成独立片段','result':'pass','findings':['有可定位的动作变化；未裁定年份'],
                      'unresolved_blockers':[],'artifacts':[{'id':text['id'],'sha256':text['sha256']}]})
        runs.add_artifact(self.project,'run-1','save-review',review,'review-1','review')
        return runs.change_stage(self.project,'run-1','finish','completed','交付已完成', 'review-1')

    def test_trial_completion_never_accepts_manuscript(self):
        before=(self.project/'版本记录/revisions.json').read_bytes();self.finish()
        self.assertEqual((self.project/'版本记录/revisions.json').read_bytes(),before)
        self.assertIsNone(runs.derive(self.project)['active_run'])
        with self.assertRaises(ValueError):runs.activate(self.project,'run-1','again')

    def test_completion_requires_review_and_scoped_blockers(self):
        self.start()
        with self.assertRaises(ValueError):runs.change_stage(self.project,'run-1','skip','completed','skip')
        runs.change_stage(self.project,'run-1','review','review','to review')
        with self.assertRaises(ValueError):runs.change_stage(self.project,'run-1','skip','completed','skip')

    def test_unrelated_issue_allows_trial_but_blocking_issue_needs_evidence(self):
        self.request['open_issues']=[{'id':'year','impact':'只影响整章年份，不影响当前独立片段','blocks_completion':False}]
        self.finish()
        self.assertEqual(runs.derive(self.project)['runs']['run-1']['stage'],'completed')

    def test_fiction_scope_and_schema_are_explicit(self):
        self.request['fiction_policy']={'mode':'reconstruction'}
        with self.assertRaises(ValueError):self.start()
        self.request['fiction_policy'].update(scope='仅本片段短对白',authorization_ref='actual-task')
        self.start()
        manifest=self.project/'版本记录/revisions.json';data=json.loads(manifest.read_text());data['schema_version']=99;write_json(manifest,data)
        with self.assertRaises(ValueError):add_revision(self.project,self.source,'x','text','1','draft')
        with self.assertRaises(ValueError):set_chapters(self.project,[])
        self.assertIn('Unsupported',validate(self.project)[0])

    def test_derived_cache_rebuild_and_event_tamper_detection(self):
        self.text();(self.project/'lifecycle/state.json').write_text('bad cache')
        self.assertEqual(runs.active_context(self.project)['state']['stage'],'draft')
        path=self.project/'lifecycle/events/00000001.json';row=json.loads(path.read_text());row['payload']['stage']='completed';write_json(path,row)
        with self.assertRaises(ValueError):runs.derive(self.project)

    def test_second_book_and_article_do_not_inherit_private_facts(self):
        self.start();second=init_project(self.root/'workspace','second','另一部合成作品','novel')
        article=init_project(self.root/'workspace','article','合成公众号文章','wechat')
        self.assertEqual(context(second)['read_full_text'],[]);self.assertIsNone(context(article)['active_task'])
        self.assertFalse((second/'runs').exists());self.assertFalse((article/'materials').exists())

    def test_existing_accepted_text_survives_new_revision_run(self):
        decision=self.project/'decision.md';decision.write_text('Synthetic fixture: accepted by synthetic author for this test only.')
        add_revision(self.project,self.source,'book-1','book_plan','1','accepted',decision_file=decision)
        add_revision(self.project,self.source,'plan-b','chapter_plan','1','accepted','scene-b','book-1',decision_file=decision)
        accepted=add_revision(self.project,self.source,'accepted-b','text','1','accepted','scene-b','plan-b',decision_file=decision)
        old_hash=accepted['sha256'];self.request['mode']='revise';self.request['stage']='revise'
        self.text()
        runs.register(self.project,'run-1','save-draft','draft-1',{'revision_id':'new-b','kind':'text','version':'1.1','status':'draft','chapter_id':'scene-b','parent_plan_id':'plan-b','based_on':'accepted-b'})
        state=derive_state(self.project)['chapters'][1]
        self.assertEqual(state['accepted_text'],'accepted-b');self.assertEqual(state['latest_text'],'new-b')
        self.assertEqual(digest(self.project/accepted['path']),old_hash)
        ctx=context(self.project)
        self.assertTrue({'accepted_text','target_text'} <= {r['role'] for r in ctx['read_full_text']})

    def test_blocking_issue_needs_unchanged_resolution_record(self):
        self.request['open_issues']=[{'id':'fact','impact':'本次输出的核心事实不明','blocks_completion':True}]
        with self.assertRaisesRegex(ValueError,'Issues still block'):self.finish()
        decision=self.project/'fact-decision.md';decision.write_text('Synthetic fixture: actual scoped resolution.')
        runs.resolve_issue(self.project,'run-1','resolve-fact','fact','fact-decision.md')
        runs.change_stage(self.project,'run-1','finish','completed','交付已完成','review-1')
        decision.write_text('tampered')
        with self.assertRaises(ValueError):runs.verify(self.project,'run-1')

    def test_unknown_metadata_fields_preserved(self):
        path=self.project/'book.yaml';meta=json.loads(path.read_text());meta['private_extension']={'scope':'local only'};write_json(path,meta)
        set_chapters(self.project,[{'id':'scene-a','title':'改名但保留身份'},{'id':'scene-b','title':'第二场'}])
        self.assertEqual(json.loads(path.read_text())['private_extension'],meta['private_extension'])
        self.assertEqual(json.loads(path.read_text())['chapters'][0]['id'],'scene-a')


if __name__=='__main__': unittest.main()
