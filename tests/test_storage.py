import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from storage import (
    atomic_write_json,
    QUARANTINE_KEEP,
    load_json_or_default,
    quarantined_copies,
    replace_json_entry,
)


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


class AcceptTest(unittest.TestCase):
    def test_a_document_the_check_rejects_is_quarantined_like_a_corrupt_one(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "users.json"
            path.write_text("[1, 2]", encoding="utf-8")
            result = load_json_or_default(path, {}, accept=lambda data: isinstance(data, dict))
            self.assertEqual(result, {})
            self.assertFalse(path.exists())
            kept = [item for item in Path(folder).iterdir() if ".corrupt_" in item.name]
            self.assertEqual([item.read_text(encoding="utf-8") for item in kept], ["[1, 2]"])

    def test_a_document_the_check_accepts_is_returned_and_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "users.json"
            path.write_text('{"ann": "x"}', encoding="utf-8")
            self.assertEqual(
                load_json_or_default(path, {}, accept=lambda data: isinstance(data, dict)), {"ann": "x"}
            )
            self.assertTrue(path.exists())

    def test_the_default_is_not_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "none.json"
            self.assertEqual(load_json_or_default(missing, 7, accept=lambda data: False), 7)


class QuarantineReportTest(unittest.TestCase):
    def test_on_quarantine_receives_the_new_path_for_corrupt_and_rejected_files(self):
        for content, accept in (("{ broken", None), ("[1]", lambda data: isinstance(data, dict))):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "data.json"
                path.write_text(content, encoding="utf-8")
                seen = []
                load_json_or_default(path, {}, accept=accept, on_quarantine=seen.append)
                self.assertEqual(len(seen), 1)
                self.assertTrue(Path(seen[0]).exists())
                self.assertIn(".corrupt_", Path(seen[0]).name)

    def test_on_quarantine_is_not_called_for_a_good_or_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            seen = []
            load_json_or_default(path, {}, on_quarantine=seen.append)
            path.write_text("{}", encoding="utf-8")
            load_json_or_default(path, {}, on_quarantine=seen.append)
            self.assertEqual(seen, [])


class QuarantineRetentionTest(unittest.TestCase):
    def corrupt_and_load(self, path, stamp, label):
        path.write_text(label, encoding="utf-8")
        with mock.patch("storage.time.time", return_value=float(stamp)):
            load_json_or_default(path, {})

    def test_only_the_newest_copies_are_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            for stamp in range(1000, 1008):
                self.corrupt_and_load(path, stamp, f"bad {{ {stamp}")
            kept = [item.name for item in quarantined_copies(path)]
            self.assertEqual(kept, [f"data.json.corrupt_{stamp}" for stamp in range(1007, 1002, -1)])
            self.assertEqual(len(kept), QUARANTINE_KEEP)

    def test_pruning_never_touches_other_files_or_the_live_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            other = Path(folder) / "other.json.corrupt_1"
            other.write_text("keep me", encoding="utf-8")
            for stamp in range(1000, 1008):
                self.corrupt_and_load(path, stamp, "bad {")
            path.write_text("{}", encoding="utf-8")
            self.assertTrue(other.exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {})

    def test_the_copy_just_made_is_never_the_one_pruned(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            for stamp in range(2000, 2006):
                self.corrupt_and_load(path, stamp, "bad {")
            # an older stamp arrives after newer ones (clock moved back): it is still kept
            self.corrupt_and_load(path, 5, "clock went back")
            self.assertTrue(any(item.name.endswith("corrupt_5") for item in quarantined_copies(path)))


class QuarantinedCopiesTest(unittest.TestCase):
    def test_lists_only_this_files_copies_newest_first(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            # modification times deliberately disagree with the stamps: a rename keeps the old mtime
            for index, name in enumerate(("data.json.corrupt_300", "data.json.corrupt_300_1",
                                          "data.json.corrupt_100", "other.json.corrupt_999", "data.json")):
                item = Path(folder) / name
                item.write_text("x", encoding="utf-8")
                os.utime(item, (1000 + index, 1000 + index))
            names = [Path(item).name for item in quarantined_copies(path)]
            self.assertEqual(names, ["data.json.corrupt_300_1", "data.json.corrupt_300", "data.json.corrupt_100"])

    def test_a_missing_folder_has_no_copies(self):
        self.assertEqual(quarantined_copies(Path("no-such-folder") / "data.json"), [])


class QuarantineCollisionTest(unittest.TestCase):
    def test_two_corrupt_files_in_the_same_second_are_both_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            with mock.patch("storage.time.time", return_value=1000.0):
                path.write_text("first {", encoding="utf-8")
                load_json_or_default(path, {})
                path.write_text("second {", encoding="utf-8")
                load_json_or_default(path, {})
            kept = sorted(
                item.read_text(encoding="utf-8") for item in Path(folder).iterdir() if ".corrupt_" in item.name
            )
            self.assertEqual(kept, ["first {", "second {"])


class ReplaceJsonEntryTest(unittest.TestCase):
    def test_replaces_only_the_named_entry_when_it_is_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "users.json"
            atomic_write_json(path, {"ann": "old", "bob": "keep"})
            self.assertTrue(replace_json_entry(path, "ann", "old", "new"))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ann": "new", "bob": "keep"})

    def test_keeps_an_entry_added_after_the_caller_read_the_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "users.json"
            atomic_write_json(path, {"ann": "old"})
            atomic_write_json(path, {"ann": "old", "late": "registered"})
            self.assertTrue(replace_json_entry(path, "ann", "old", "new"))
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")), {"ann": "new", "late": "registered"}
            )

    def test_leaves_the_file_alone_when_the_entry_changed_or_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "users.json"
            atomic_write_json(path, {"ann": "changed"})
            self.assertFalse(replace_json_entry(path, "ann", "old", "new"))
            self.assertFalse(replace_json_entry(path, "ghost", "old", "new"))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"ann": "changed"})


if __name__ == "__main__":
    unittest.main()
