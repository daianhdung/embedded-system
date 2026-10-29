from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_submission import package

class PackageTests(unittest.TestCase):
    def test_bundle_has_portable_ledger_but_no_private_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'submission.zip'
            result=package(path)
            with zipfile.ZipFile(path) as archive:
                names=archive.namelist()
                self.assertIn('PCCC/acceptance/integration-results.csv',names)
                self.assertIn('PCCC/dashboard/app.py',names)
                self.assertFalse(any('/runs/' in n or '/.venv' in n or n.endswith(('.pt','.pyc','/secrets.h')) for n in names))
            self.assertFalse(result['report_included'])
            with self.assertRaises(FileExistsError):package(path)
