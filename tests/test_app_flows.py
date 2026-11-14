"""End-to-end checks that drive main.py through Streamlit's AppTest in a throwaway folder."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

PROJECT = Path(__file__).resolve().parent.parent
MAIN = str(PROJECT / "main.py")


class AppFlowCase(unittest.TestCase):
    """Runs each test inside its own temp folder so local state files never touch the repo."""

    def setUp(self):
        previous = os.getcwd()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.addCleanup(os.chdir, previous)
        os.chdir(self.folder.name)

    def write(self, name, text):
        Path(self.folder.name, name).write_text(text, encoding="utf-8")

    def new_app(self):
        return AppTest.from_file(MAIN, default_timeout=60)

    def log_in(self, username, password):
        app = self.new_app().run()
        app.text_input(key="login_user").set_value(username)
        app.text_input(key="login_pass").set_value(password)
        app.button[0].click().run()
        return app


class LegacyLoginTest(AppFlowCase):
    def test_legacy_account_with_a_long_password_can_log_in(self):
        password = "p" * 80
        self.write("users_db.json", json.dumps({"olduser": hashlib.sha256(password.encode()).hexdigest()}))
        app = self.log_in("olduser", password)
        self.assertEqual([item.value for item in app.exception], [])
        self.assertTrue(app.session_state["logged_in"])

    def test_legacy_account_with_a_short_password_is_upgraded_to_bcrypt(self):
        self.write("users_db.json", json.dumps({"olduser": hashlib.sha256(b"shortpass1").hexdigest()}))
        app = self.log_in("olduser", "shortpass1")
        self.assertTrue(app.session_state["logged_in"])
        stored = json.loads(Path(self.folder.name, "users_db.json").read_text(encoding="utf-8"))
        self.assertTrue(stored["olduser"].startswith("$2"))


if __name__ == "__main__":
    unittest.main()
