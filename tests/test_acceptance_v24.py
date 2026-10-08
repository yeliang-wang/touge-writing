"""New release scope and independent evidence cannot be satisfied by empty claims."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from acceptance_v24 import config, independent_behavior, publication_evidence, output_directory
from workspace_lib import write_json, digest


class AcceptanceV24Test(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'VERSION').write_text('2.4.0\n')
        self.cfg = json.loads((ROOT / 'configs/acceptance-v2.4.json').read_text())
        write_json(self.root / 'configs/acceptance-v2.4.json', self.cfg)

    def test_scope_cannot_lose_private_checks_or_duplicate_ids(self):
        self.assertEqual(config(self.root)['version'], '2.4.0')
        self.cfg['checks'][-1] = self.cfg['checks'][0]
        write_json(self.root / 'configs/acceptance-v2.4.json', self.cfg)
        with self.assertRaises(ValueError): config(self.root)

    def test_behavior_requires_real_artifacts_and_current_files(self):
        folder = self.root / 'evals/v2.4/rules-behavior'
        report = {'source':'independent_agent_forward_test','all_in_scope_passed':True,
                  'cases':[{'id':i,'status':'passed','observations':['Synthetic behavior']} for i in ['novel','article']],
                  'artifacts':[], 'evaluated_files':[], 'real_manuscripts_modified':False,'author_approval_claimed':False}
        write_json(folder / 'result.json',report)
        with self.assertRaisesRegex(ValueError, 'Artifact inventory'): independent_behavior(self.root)
        (folder/'observations.md').write_text('Synthetic artifact.\n')
        report['artifacts']=[{'path':'observations.md','sha256':digest(folder/'observations.md')}]
        write_json(folder/'result.json',report)
        with self.assertRaisesRegex(ValueError, 'implementation identity'): independent_behavior(self.root)

    def test_config_version_matches_product(self):
        (self.root/'VERSION').write_text('2.4.1\n')
        with self.assertRaisesRegex(ValueError,'Version/config'): config(self.root)

    def test_patch_has_separate_config_behavior_and_outputs(self):
        workspace = self.root / 'private'
        self.assertEqual(output_directory(workspace, root=self.root), workspace/'acceptance-v2.4.0')
        (self.root/'VERSION').write_text('2.4.1\n')
        cfg = json.loads((ROOT/'configs/acceptance-v2.4.1.json').read_text())
        write_json(self.root/'configs/acceptance-v2.4.1.json', cfg)
        self.assertEqual(config(self.root)['version'], '2.4.1')
        self.assertEqual(output_directory(workspace, root=self.root), workspace/'acceptance-v2.4.1')
        self.assertEqual(output_directory(workspace, True, self.root), self.root/'work/acceptance-public-v2.4.1')
        # A prior release's evidence cannot satisfy the patch.
        write_json(self.root/'evals/v2.4/rules-behavior/result.json', {'all_in_scope_passed': True})
        with self.assertRaises(FileNotFoundError): independent_behavior(self.root)

    def test_patch_requires_affected_method_pins_and_all_cases(self):
        (self.root/'VERSION').write_text('2.4.1\n')
        cfg = json.loads((ROOT/'configs/acceptance-v2.4.1.json').read_text())
        write_json(self.root/'configs/acceptance-v2.4.1.json', cfg)
        folder=self.root/'evals/v2.4.1/rules-behavior'
        report={'source':'independent_agent_forward_test','all_in_scope_passed':True,
                'cases':[{'id':i,'status':'passed','observations':['Synthetic execution']} for i in cfg['behavior_case_ids']],
                'artifacts':[], 'evaluated_files':[], 'real_manuscripts_modified':False,'author_approval_claimed':False}
        write_json(folder/'result.json', report)
        (folder/'actual.md').write_text('A synthetic saved result.\n')
        report['artifacts']=[{'path':'actual.md','sha256':digest(folder/'actual.md')}]
        base=['.agents/skills/touge-novel-writing/SKILL.md','.agents/skills/touge-wechat-writing/SKILL.md',
              'scripts/writing_rules.py','scripts/writing_workspace.py','scripts/writing_run.py']
        for relative in base+cfg['behavior_required_files']:
            path=self.root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('Synthetic implementation\n')
        report['evaluated_files']=[{'path':p,'sha256':digest(self.root/p)} for p in base]
        write_json(folder/'result.json', report)
        with self.assertRaisesRegex(ValueError,'implementation identity'): independent_behavior(self.root)
        report['evaluated_files'] += [{'path':p,'sha256':digest(self.root/p)} for p in cfg['behavior_required_files']]
        write_json(folder/'result.json', report)
        self.assertEqual(independent_behavior(self.root)['cases'],3)
        (self.root/cfg['behavior_required_files'][1]).write_text('Changed method\n')
        with self.assertRaisesRegex(ValueError,'older implementation'): independent_behavior(self.root)
        report['cases'].pop(); write_json(folder/'result.json', report)
        with self.assertRaisesRegex(ValueError,'scope missing'): independent_behavior(self.root)

    def test_release_version_cannot_select_arbitrary_paths(self):
        for version in ['2.4.01','2.5.0','../../other']:
            (self.root/'VERSION').write_text(version+'\n')
            with self.assertRaisesRegex(ValueError,'Unsupported'): config(self.root)

    def publication_fixture(self):
        repos = {}
        for name in ['public', 'private']:
            origin = self.root / name
            origin.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(origin), *args], stderr=subprocess.DEVNULL, text=True).strip()
            git('init', '-b', 'main'); git('config', 'user.name', 'Synthetic Tester'); git('config', 'user.email', 'test@example.invalid')
            (origin/'README.md').write_text(name)
            git('add', '.'); git('commit', '-m', 'Synthetic fixture')
            clone = self.root / (name + '-clone')
            subprocess.check_call(['git','clone',str(origin),str(clone)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            head = git('rev-parse','HEAD')
            repos[name] = {'clone':str(clone),'commit':head,'remote_head':head,
                           'visibility':'PRIVATE' if name == 'private' else 'PUBLIC',
                           'tracked_files':{'README.md':digest(origin/'README.md')}}
        fake = self.root/'not-a-release.zip'; fake.write_text('not an actual published archive')
        receipt = dict(repos, release_asset={'built':str(fake),'download':str(fake),'sha256':digest(fake)},
                       tag_commit=repos['public']['commit'],release_url='https://example.invalid/not-published')
        out = self.root/'receipts'; write_json(out/'publication.json',receipt)
        return receipt,out

    def test_local_clones_and_self_reported_remote_do_not_prove_publication(self):
        receipt,out = self.publication_fixture()
        with patch('acceptance_v24.ROOT',self.root/'public'):
            with self.assertRaisesRegex(ValueError,'actual GitHub origin'):
                publication_evidence(self.root/'private',out)

    def test_live_visibility_overrides_receipt_claim(self):
        receipt,out = self.publication_fixture()
        clone=receipt['public']['clone']
        subprocess.check_call(['git','-C',clone,'remote','set-url','origin','https://github.com/synthetic/demo.git'])
        from acceptance_v24 import _external
        def response(argv):
            if argv[:3] == ['gh','repo','view']:
                return json.dumps({'nameWithOwner':'synthetic/demo','visibility':'PRIVATE','defaultBranchRef':{'name':'main'}})
            return _external(argv)
        with patch('acceptance_v24.ROOT',self.root/'public'), patch('acceptance_v24._external',side_effect=response):
            with self.assertRaisesRegex(ValueError,'Live GitHub visibility'):
                publication_evidence(self.root/'private',out)
