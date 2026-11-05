import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from exports import download_font, escape_ics_text, generate_ics


class IcsEscapingTest(unittest.TestCase):
    def test_escapes_text_separators_and_newlines(self):
        self.assertEqual(
            escape_ics_text("A, B; C\\ D\nE"),
            "A\\, B\\; C\\\\ D\\nE",
        )

    def test_generated_event_escapes_personnel_names(self):
        schedule = {date(2026, 2, 1): [{"name": "Ada, M\nBEGIN:VEVENT"}]}

        payload = generate_ics(schedule).decode("utf-8")

        self.assertIn("SUMMARY:Duty Roster: Ada\\, M\\nBEGIN:VEVENT", payload)
        self.assertEqual(payload.count("\nBEGIN:VEVENT"), 1)

    def test_generated_events_carry_uid_and_dtstamp(self):
        schedule = {
            date(2026, 2, 1): [{"name": "Ada"}],
            date(2026, 2, 2): [{"name": "Bo"}],
        }

        payload = generate_ics(schedule).decode("utf-8")

        self.assertEqual(payload.count("\nUID:"), 2)
        self.assertEqual(payload.count("\nDTSTAMP:"), 2)
        uids = [line for line in payload.splitlines() if line.startswith("UID:")]
        self.assertEqual(len(set(uids)), 2)

    def test_generated_uid_is_stable_for_the_same_event(self):
        schedule = {date(2026, 2, 1): [{"name": "Ada"}]}

        first = generate_ics(schedule).decode("utf-8")
        second = generate_ics(schedule).decode("utf-8")
        first_uid = [line for line in first.splitlines() if line.startswith("UID:")]
        second_uid = [line for line in second.splitlines() if line.startswith("UID:")]

        self.assertEqual(first_uid, second_uid)


class DownloadFontTest(unittest.TestCase):
    def test_existing_font_is_not_downloaded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            path.write_bytes(b"cached")

            with mock.patch("exports.urllib.request.urlopen") as urlopen:
                download_font("https://example.invalid/font.ttf", path)

            urlopen.assert_not_called()
            self.assertEqual(path.read_bytes(), b"cached")

    def test_download_uses_a_timeout_and_replaces_the_target(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b"font-bytes"

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            with mock.patch("exports.urllib.request.urlopen", return_value=Response()) as urlopen:
                download_font("https://example.invalid/font.ttf", path)

            urlopen.assert_called_once_with("https://example.invalid/font.ttf", timeout=10)
            self.assertEqual(path.read_bytes(), b"font-bytes")
            self.assertFalse(Path(str(path) + ".tmp").exists())
            leftovers = [p for p in Path(folder).iterdir() if p.name != path.name]
            self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
