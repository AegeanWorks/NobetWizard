import hashlib
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from exports import (
    FONT_MAX_BYTES,
    ROBOTO_BOLD,
    ROBOTO_REGULAR,
    download_font,
    escape_ics_text,
    generate_ics,
)


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

    def test_generated_ics_uses_crlf_and_folds_long_lines(self):
        schedule = {date(2026, 2, 1): [{"name": "A" * 100}]}

        payload = generate_ics(schedule).decode("utf-8")

        self.assertNotIn("\n", payload.replace("\r\n", ""))
        for line in payload.split("\r\n"):
            self.assertLessEqual(len(line.encode("utf-8")), 75)
        self.assertIn("SUMMARY:Duty Roster: ", payload.replace("\r\n ", ""))


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.requested = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        self.requested = size
        return self.payload if size < 0 else self.payload[:size]


class DownloadFontTest(unittest.TestCase):
    URL = "https://example.invalid/font.ttf"

    def download(self, folder, payload, expected, **options):
        path = Path(folder) / "Roboto.ttf"
        with mock.patch("exports.urllib.request.urlopen", return_value=FakeResponse(payload)) as urlopen:
            download_font(self.URL, path, expected, **options)
        return path, urlopen

    def test_existing_font_with_the_expected_hash_is_not_downloaded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            path.write_bytes(b"cached")
            with mock.patch("exports.urllib.request.urlopen") as urlopen:
                download_font(self.URL, path, sha256(b"cached"))
            urlopen.assert_not_called()
            self.assertEqual(path.read_bytes(), b"cached")

    def test_existing_font_with_another_hash_is_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Roboto.ttf"
            path.write_bytes(b"tampered")
            with mock.patch("exports.urllib.request.urlopen", return_value=FakeResponse(b"font-bytes")):
                download_font(self.URL, path, sha256(b"font-bytes"))
            self.assertEqual(path.read_bytes(), b"font-bytes")

    def test_download_uses_a_timeout_and_replaces_the_target(self):
        with tempfile.TemporaryDirectory() as folder:
            path, urlopen = self.download(folder, b"font-bytes", sha256(b"font-bytes"))
            urlopen.assert_called_once_with(self.URL, timeout=10)
            self.assertEqual(path.read_bytes(), b"font-bytes")
            leftovers = [p for p in Path(folder).iterdir() if p.name != path.name]
            self.assertEqual(leftovers, [])

    def test_a_payload_with_another_hash_is_refused_and_leaves_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                self.download(folder, b"tampered", sha256(b"font-bytes"))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_a_payload_over_the_size_cap_is_refused_and_leaves_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = b"x" * 11
            with self.assertRaises(ValueError):
                self.download(folder, payload, sha256(payload), max_bytes=10)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_a_payload_exactly_at_the_cap_is_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            payload = b"x" * 10
            path, _ = self.download(folder, payload, sha256(payload), max_bytes=10)
            self.assertEqual(path.read_bytes(), payload)

    def test_the_read_is_bounded_by_the_cap(self):
        response = FakeResponse(b"x" * 5)
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch("exports.urllib.request.urlopen", return_value=response):
                download_font(self.URL, Path(folder) / "f.ttf", sha256(b"x" * 5), max_bytes=10)
        self.assertEqual(response.requested, 11)


class PinnedFontsTest(unittest.TestCase):
    def test_fonts_are_pinned_to_a_commit_with_a_sha256(self):
        for url, digest in (ROBOTO_REGULAR, ROBOTO_BOLD):
            self.assertTrue(url.startswith("https://raw.githubusercontent.com/googlefonts/roboto-2/"))
            self.assertRegex(url, r"/[0-9a-f]{40}/src/hinted/Roboto-(Regular|Bold)\.ttf$")
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_the_cap_leaves_room_for_the_real_fonts(self):
        self.assertGreater(FONT_MAX_BYTES, 515100)
        self.assertLessEqual(FONT_MAX_BYTES, 4 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
