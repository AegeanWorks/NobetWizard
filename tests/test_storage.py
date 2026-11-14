import json
import tempfile
import unittest
from pathlib import Path

from storage import atomic_write_json, load_json_or_default


class LoadJsonOrDefaultTest(unittest.TestCase):
    def test_reads_an_existing_document(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text('{"personnel": [1, 2]}', encoding="utf-8")

            self.assertEqual(load_json_or_default(path, {"personnel": []}), {"personnel": [1, 2]})

    def test_missing_file_returns_the_default(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"

            self.assertEqual(load_json_or_default(path, {"personnel": []}), {"personnel": []})
            self.assertFalse(path.exists())

    def test_corrupt_file_is_quarantined_and_default_returned(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "personnel_db_user.json"
            path.write_text('{"personnel": [ {"name": "P1",', encoding="utf-8")

            result = load_json_or_default(path, {"personnel": []})

            self.assertEqual(result, {"personnel": []})
            self.assertFalse(path.exists())
            quarantined = [item for item in Path(folder).iterdir() if ".corrupt_" in item.name]
            self.assertEqual(len(quarantined), 1)
            self.assertIn('{"personnel"', quarantined[0].read_text(encoding="utf-8"))


class AtomicWriteJsonTest(unittest.TestCase):
    def test_writes_and_overwrites_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            atomic_write_json(path, {"first": 1})
            atomic_write_json(path, {"second": [1, 2]})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"second": [1, 2]})

    def test_leaves_no_temporary_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            atomic_write_json(path, {"ok": True})

            self.assertEqual([p.name for p in Path(folder).iterdir()], ["data.json"])

    def test_creates_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested" / "data.json"
            atomic_write_json(path, {"ok": True})

            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
