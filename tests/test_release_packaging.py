"""Current package identity and deterministic extraction remain portable."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_release


class ReleasePackagingTest(unittest.TestCase):
    def test_renamed_distribution_preserves_content_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'public'; root.mkdir()
            (root / 'VERSION').write_text('2.3.1\n')
            (root / 'README.md').write_text('# Synthetic public writing toolkit\n')
            outputs = [Path(temporary) / 'one.zip', Path(temporary) / 'two.zip']
            with patch.object(build_release, 'audit_public', return_value=[]), \
                    patch.object(build_release, 'public_paths', return_value=['VERSION', 'README.md']):
                results = [build_release.build(path, root) for path in outputs]
            self.assertEqual(results[0]['sha256'], results[1]['sha256'])
            with zipfile.ZipFile(outputs[0]) as archive:
                prefix = 'touge-writing-2.3.1/'
                self.assertEqual(set(archive.namelist()),
                                 {prefix + name for name in ['VERSION', 'README.md', 'release-manifest.json']})
                self.assertEqual(archive.read(prefix + 'README.md'), (root / 'README.md').read_bytes())
                manifest = json.loads(archive.read(prefix + 'release-manifest.json'))
                self.assertEqual(manifest['version'], '2.3.1')
                self.assertFalse(manifest['workspace_included'])
                self.assertEqual({r['path'] for r in manifest['files']}, {'VERSION', 'README.md'})


if __name__ == '__main__':
    unittest.main()
