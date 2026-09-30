import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workspace_lib import digest, scoped_path, write_json, read_json, immutable_copy, write_lock
from writing_workspace import init_project, set_chapters, add_revision, derive_state, context, validate, retrieve
from migrate_workspace import migrate, verify
from backup_workspace import create, restore
from external_operations import prepare, record_result
from manuscript_check import check
from preflight_check import audit_public
from export_author_profile import export


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / 'workspace'
        self.source = self.root / 'source.md'
        self.source.write_text('一段可核对的测试资料。代码启蒙与职业选择。')
        self.decision = self.root / 'decision.md'
        self.decision.write_text('Synthetic fixture: author approves this test revision.')

    def tearDown(self):
        self.tmp.cleanup()

    def novel(self, name='book-one'):
        p = init_project(self.workspace, name, name, 'novel')
        set_chapters(p, [{'id':'ch01','title':'第一章'},{'id':'ch02','title':'第二章'}])
        return p

    def accept(self,p,rid,kind,parent=None,chapter=None,based=None):
        return add_revision(p,self.source,rid,kind,'1.0','accepted',chapter,parent,based,self.decision)

    def test_migration_is_idempotent_and_detects_tampering(self):
        plan={'schema_version':1,'migration_id':'test','entries':[{'source':str(self.source),'destination':'archives/source.md','sha256':digest(self.source),'source_id':'test'}]}
        receipt=migrate(plan,self.workspace)
        self.assertEqual(migrate(plan,self.workspace)['files'],1)
        self.assertEqual(verify(receipt,self.workspace,True),[])
        self.source.write_text('changed')
        self.assertTrue(verify(receipt,self.workspace,True))
        with self.assertRaises(ValueError):migrate(plan,self.workspace)
        self.assertNotEqual((self.workspace/'archives/source.md').read_text(), 'changed')

    def test_paths_cannot_escape_or_follow_external_symlink(self):
        self.workspace.mkdir()
        for rel in ['../outside','/outside']:
            with self.assertRaises(ValueError):scoped_path(self.workspace,rel)
        (self.workspace/'link').symlink_to(self.root)
        with self.assertRaises(ValueError):scoped_path(self.workspace,'link/source.md')

    def test_immutable_copy_refuses_overwrite(self):
        target=self.root/'target.md';target.write_text('existing')
        with self.assertRaises(ValueError):immutable_copy(self.source,target)
        self.assertEqual(target.read_text(),'existing')

    def test_historical_plan_inheritance_and_next_action(self):
        p=self.novel()
        self.accept(p,'bp1','book_plan')
        self.accept(p,'cp1','chapter_plan','bp1','ch01')
        self.accept(p,'text1','text','cp1','ch01')
        self.accept(p,'bp2','book_plan',based='bp1')
        state=derive_state(p)
        self.assertEqual(state['book_plan'],'bp2')
        self.assertEqual(state['next_action'],{'chapter_id':'ch02','action':'review_chapter_plan'})
        result=context(p,'ch01')
        self.assertTrue(any(r['id']=='bp1' and r['role']=='historical_inheritance' for r in result['read_full_text']))
        self.assertEqual(validate(p),[])

    def test_acceptance_requires_actual_evidence_and_chapter_parent(self):
        p=self.novel();self.accept(p,'bp1','book_plan');self.accept(p,'cp1','chapter_plan','bp1','ch01')
        with self.assertRaises(ValueError):add_revision(p,self.source,'bad','text','1','accepted','ch01','cp1')
        with self.assertRaises(ValueError):self.accept(p,'bad','text','cp1','ch02')
        other=self.novel('book-two')
        with self.assertRaises(ValueError):self.accept(other,'bad','text','cp1','ch01')
        self.assertEqual(len(read_json(other/'版本记录/revisions.json')['revisions']),0)

    def test_revision_and_acceptance_tampering_detected(self):
        p=self.novel();r=self.accept(p,'bp1','book_plan')
        (p/r['decision_path']).write_text('altered approval')
        self.assertTrue(validate(p))
        with self.assertRaises(ValueError):context(p)

    def test_no_duplicate_revision_and_no_cyclic_predecessor(self):
        p=self.novel();self.accept(p,'bp1','book_plan')
        with self.assertRaises(ValueError):self.accept(p,'bp1','book_plan')
        path=p/'版本记录/revisions.json';m=read_json(path);m['revisions'][0]['based_on']='bp1';write_json(path,m)
        self.assertTrue(validate(p))

    def test_state_cache_is_rebuildable(self):
        p=self.novel();self.accept(p,'bp1','book_plan')
        (p/'state.json').write_text('broken cache')
        self.assertEqual(context(p)['state']['book_plan'],'bp1')

    def test_search_excludes_old_versions_and_other_projects(self):
        p=self.novel();other=self.novel('book-two')
        add_revision(p,self.source,'old','text','0.1','historical','ch01')
        self.source.write_text('测试正文里只有数据库查询。')
        add_revision(p,self.source,'new','text','0.2','draft','ch01')
        self.source.write_text('代码启蒙与职业选择的另一部作品。')
        add_revision(other,self.source,'foreign','text','1','draft','ch01')
        self.assertEqual(retrieve(p,'代码启蒙'),[])
        self.assertEqual([r['id'] for r in retrieve(p,'代码启蒙',True)],['old'])

    def test_project_writes_are_locked(self):
        p=self.novel()
        with write_lock(p):
            with self.assertRaises(ValueError):self.accept(p,'bp1','book_plan')
        self.assertEqual(validate(p),[])

    def test_cannot_remove_used_chapter(self):
        p=self.novel();add_revision(p,self.source,'t1','text','0.1','baseline','ch01')
        with self.assertRaises(ValueError):set_chapters(p,[{'id':'ch02','title':'two'}])

    def test_wechat_article_is_independent(self):
        p=init_project(self.workspace,'article','文章','wechat')
        self.accept(p,'v1','text')
        self.assertEqual(context(p)['read_full_text'][0]['id'],'v1')
        self.assertEqual(validate(p),[])

    def test_remote_retry_and_evidence_integrity(self):
        p=init_project(self.workspace,'article','文章','wechat');r=self.accept(p,'v1','text')
        op=prepare(p,'test-service','personal','create','v1')
        self.assertTrue(prepare(p,'test-service','personal','create','v1')['retry_requires_reconciliation'])
        evidence=self.root/'evidence.json'
        base={'source':'live_mcp','service':'test-service','operation_id':op['operation_id'],'account_alias':'personal','local_sha256':r['sha256'],'remote_id':'test-doc','readback_matches':False,'response':{'test_fixture':True}}
        write_json(evidence,base)
        with self.assertRaises(ValueError):record_result(p,op['operation_id'],'verified',evidence,'test-doc')
        record_result(p,op['operation_id'],'unknown',evidence,'test-doc')
        base['readback_matches']=True;base['account_alias']='wrong';write_json(evidence,base)
        with self.assertRaises(ValueError):record_result(p,op['operation_id'],'verified',evidence,'test-doc')
        base['account_alias']='personal';write_json(evidence,base)
        self.assertEqual(record_result(p,op['operation_id'],'verified',evidence,'test-doc')['status'],'verified')
        with self.assertRaises(ValueError):record_result(p,op['operation_id'],'failed',evidence)
        with self.assertRaises(ValueError):prepare(p,'test-service','personal','update','v1','test-doc')

    def test_backup_restore_exact_and_non_destructive(self):
        self.novel();out=self.root/'backup.tar.gz';created=create(self.workspace,out)
        dest=self.root/'restored';r=restore(out,dest)
        self.assertTrue(r['verified_restore']);self.assertEqual(created['files'],r['files'])
        self.assertEqual(digest(self.workspace/'catalog.json'),digest(dest/'catalog.json'))
        with self.assertRaises(ValueError):restore(out,dest)
        with out.open('ab') as f:f.write(b'tamper')
        with self.assertRaises(ValueError):restore(out,self.root/'bad-restore')

    def test_restore_rejects_traversal_even_with_valid_archive_digest(self):
        out=self.root/'bad.tar.gz'
        with tarfile.open(out,'w:gz') as z:
            for name,body in [('backup-manifest.json',b'{"files":[]}'),('../escape',b'x')]:
                info=tarfile.TarInfo(name);info.size=len(body);z.addfile(info,io.BytesIO(body))
        write_json(str(out)+'.json',{'sha256':digest(out)})
        with self.assertRaises(ValueError):restore(out,self.root/'restored')
        self.assertFalse((self.root/'escape').exists())

    def test_backup_rejects_workspace_symlink(self):
        self.workspace.mkdir();(self.workspace/'secret').symlink_to(self.source)
        with self.assertRaises(ValueError):create(self.workspace,self.root/'b.tar.gz')

    def test_scan_includes_structure_in_headings_and_quotes(self):
        r=check('# 第一章 入行\n## 幕一 地下室\n> 收束\n正文正文正文正文正文正文正文正文')
        self.assertEqual({x['marker'] for x in r['structural_word_findings']},{'幕一','收束'})
        self.assertTrue(r['repeated_windows']);self.assertFalse(r['facts_verified'])

    def test_profile_export_allowlist_and_hashes(self):
        profile=self.root/'profile';shutil.copytree(ROOT/'shared/author-expression',profile)
        (profile/'private.md').write_text('must not export')
        out=self.root/'profile.zip';export(profile,out)
        duplicate=self.root/'profile-again.zip';export(profile,duplicate)
        self.assertEqual(digest(out),digest(duplicate))
        with zipfile.ZipFile(out) as z:
            self.assertEqual(len(z.namelist()),8)
            self.assertFalse(any('private.md' in n for n in z.namelist()))
        (profile/'language.md').write_text('unreviewed change')
        with self.assertRaises(ValueError):export(profile,self.root/'changed.zip')

    def test_public_check_catches_forced_private_files_and_staged_secret(self):
        repo=self.root/'repo';repo.mkdir()
        def git(*args):return subprocess.run(['git','-C',str(repo),*args],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        git('init');(repo/'.gitignore').write_text('workspace/\n');(repo/'workspace').mkdir()
        (repo/'workspace/private.md').write_text('private');git('add','.gitignore')
        self.assertEqual(audit_public(repo),[])
        git('add','-f','workspace/private.md')
        self.assertTrue(audit_public(repo));git('reset','--','workspace/private.md')
        public=repo/'example.txt';public.write_text('Authorization: '+'a'*32);git('add','example.txt');public.write_text('clean working copy')
        self.assertTrue(any('index' in e for e in audit_public(repo)))


if __name__=='__main__': unittest.main()
