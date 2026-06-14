import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ai_chi.forge.intake import inspect_zip
from ai_chi.forge.audit import detect_manifest_quality, scan_zip_text, recommend_status


class ArtifactForgeTests(unittest.TestCase):
    def test_inspect_zip(self):
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "sample.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("README.md", "# Test\n")
                z.writestr("EXPORT_MANIFEST.md", "# Manifest\n")

            records = inspect_zip(zp)
            self.assertEqual(len(records), 2)
            self.assertTrue(any(r.path == "README.md" for r in records))
            self.assertEqual(detect_manifest_quality(records), "present_unverified")

    def test_reject_zip_slip(self):
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "evil.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("../evil.txt", "bad")

            with self.assertRaises(ValueError):
                inspect_zip(zp)

    def test_overclaim_scan(self):
        with tempfile.TemporaryDirectory() as td:
            zp = Path(td) / "claim.zip"
            with zipfile.ZipFile(zp, "w") as z:
                z.writestr("README.md", "This is production-ready and fully self-contained.")

            records = inspect_zip(zp)
            scans = scan_zip_text(zp, records)
            self.assertGreaterEqual(len(scans["overclaims"]), 1)


if __name__ == "__main__":
    unittest.main()
