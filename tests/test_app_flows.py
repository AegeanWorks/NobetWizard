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


PERSON = {
    "name": "Ann", "gender": "F", "role": "Senior", "fixed_duties_total": 0, "fixed_duties_weekend": 0,
    "max_duties": 20, "max_weekends": 10, "mixed_gender_allowed": True, "busy_days": "", "off_dates": "",
    "leave_dates": "", "fixed_dates": "", "duty_count": 0, "weekend_duty_count": 0,
}


class MalformedPersonnelStateTest(AppFlowCase):
    def open_page(self, raw):
        self.write("personnel_db_probe.json", raw)
        app = self.new_app()
        app.session_state["logged_in"] = True
        app.session_state["username"] = "probe"
        return app.run()

    def quarantined(self):
        return [name for name in os.listdir(self.folder.name) if ".corrupt_" in name]

    def test_unusable_shapes_are_quarantined_and_the_page_loads(self):
        for raw in ("5", '{"personnel": null}'):
            with self.subTest(raw=raw):
                for name in self.quarantined():
                    os.remove(os.path.join(self.folder.name, name))
                app = self.open_page(raw)
                self.assertEqual([item.value for item in app.exception], [])
                self.assertEqual(len(self.quarantined()), 1)
                self.assertEqual(app.session_state["personnel"], [])

    def test_unusable_people_are_dropped_with_a_warning_and_the_file_is_kept(self):
        raw = json.dumps({"personnel": [PERSON, 1, {"name": "NoGender"}]})
        app = self.open_page(raw)
        self.assertEqual([item.value for item in app.exception], [])
        self.assertEqual([p["name"] for p in app.session_state["personnel"]], ["Ann"])
        self.assertTrue(any("2" in item.value for item in app.warning))
        self.assertEqual(self.quarantined(), [])

    def test_bad_settings_do_not_crash_the_page(self):
        for key, value in (("conditional_rules", 5), ("cfg_year", "x")):
            with self.subTest(key=key):
                app = self.open_page(json.dumps({"personnel": [PERSON], key: value}))
                self.assertEqual([item.value for item in app.exception], [])

    def test_a_person_without_limits_gets_defaults(self):
        record = {k: v for k, v in PERSON.items() if k not in ("max_duties", "max_weekends")}
        app = self.open_page(json.dumps({"personnel": [record]}))
        self.assertEqual([item.value for item in app.exception], [])
        self.assertEqual((app.session_state["personnel"][0]["max_duties"]), 5)


class MalformedUsersStateTest(AppFlowCase):
    def test_unusable_users_files_are_quarantined_and_login_fails_cleanly(self):
        for raw in ("5", '["olduser"]'):
            with self.subTest(raw=raw):
                self.write("users_db.json", raw)
                app = self.log_in("olduser", "whatever12")
                self.assertEqual([item.value for item in app.exception], [])
                self.assertFalse(app.session_state["logged_in"])
                self.assertFalse(Path(self.folder.name, "users_db.json").exists())
                for name in os.listdir(self.folder.name):
                    if ".corrupt_" in name:
                        os.remove(os.path.join(self.folder.name, name))


if __name__ == "__main__":
    unittest.main()
