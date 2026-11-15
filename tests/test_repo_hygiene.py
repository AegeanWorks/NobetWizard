"""Tracked files must not carry absolute paths from a developer's machine (G-001, ADR-027)."""
import re
import subprocess
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
# A Windows drive path into a user's home, in plain or JSON-escaped form, or a POSIX home path.
HOME_PATH = re.compile(r"[A-Za-z]:(?:\\{1,2}|/)Users(?:\\{1,2}|/)[^\\/\"\s]+|/(?:home|Users)/[^/\"\s]+/")
# Text that may legitimately show the pattern itself.
EXEMPT = {"tests/test_repo_hygiene.py"}


def tracked_text_files():
    listed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=PROJECT, capture_output=True, check=True, timeout=30
    ).stdout.decode("utf-8").split("\0")
    for name in filter(None, listed):
        path = PROJECT / name
        if name in EXEMPT or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data[:4096]:
            continue  # binary
        yield name, data.decode("utf-8", errors="replace")


class NoHomePathsTest(unittest.TestCase):
    def test_no_tracked_file_names_a_home_directory(self):
        found = []
        for name, text in tracked_text_files():
            for number, line in enumerate(text.splitlines(), 1):
                if HOME_PATH.search(line):
                    found.append(f"{name}:{number}")
        self.assertEqual(found, [], "absolute home paths in tracked files; store paths relative to the project")

    def test_the_pattern_catches_the_forms_seen_so_far(self):
        for sample in ('"C:\\\\Users\\\\someone\\\\Desktop"', "C:\\Users\\someone\\x", "C:/Users/someone/x",
                       "/home/someone/project", "/Users/someone/project"):
            self.assertRegex(sample, HOME_PATH)
        for sample in (".aikit\\\\reforge.reviews\\\\stage.md", '"roots": ["."]', "src/Users.py", "C:\\Windows"):
            self.assertNotRegex(sample, HOME_PATH)


if __name__ == "__main__":
    unittest.main()
