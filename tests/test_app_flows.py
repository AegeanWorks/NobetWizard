"""End-to-end checks that drive main.py through Streamlit's AppTest in a throwaway folder."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from streamlit.testing.v1 import AppTest

from security import check_hashes, make_hashes
from state_documents import LANGUAGES

PROJECT = Path(__file__).resolve().parent.parent
MAIN = str(PROJECT / "main.py")
FAST_BCRYPT_ROUNDS = 4  # bcrypt's minimum cost; production uses the library default


def _skip_component_scan():
    """Streamlit scans every installed package for v2 component manifests on each AppTest run.

    That scan is most of the run time and the app declares no components. Returns a patcher, or
    None when this Streamlit version has no such scanner, in which case tests run unpatched.
    """
    try:
        from streamlit.components.v2 import manifest_scanner
    except ImportError:
        return None
    if not hasattr(manifest_scanner, "scan_component_manifests"):
        return None
    return mock.patch.object(manifest_scanner, "scan_component_manifests", return_value=[])


def _fast_bcrypt():
    """Hash with the minimum cost inside tests; the stored format and checks are unchanged."""
    import bcrypt

    real = bcrypt.gensalt
    return mock.patch.object(bcrypt, "gensalt", lambda rounds=FAST_BCRYPT_ROUNDS, prefix=b"2b": real(
        min(rounds, FAST_BCRYPT_ROUNDS), prefix))


class AppFlowCase(unittest.TestCase):
    """Runs each test inside its own temp folder so local state files never touch the repo."""

    def setUp(self):
        previous = os.getcwd()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.addCleanup(os.chdir, previous)
        os.chdir(self.folder.name)
        for patcher in (_skip_component_scan(), _fast_bcrypt()):
            if patcher is not None:
                patcher.start()
                self.addCleanup(patcher.stop)

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


class RegistrationTest(AppFlowCase):
    def register(self, username, password="longenough1", admin=None):  # aikit:allow-secret[Hardcoded password assignment] -- test fixture password, not a credential
        app = self.new_app()
        if admin:
            app.secrets["admin"] = admin
        app.run()
        app.text_input(key="reg_user").set_value(username)
        app.text_input(key="reg_pass").set_value(password)
        [button for button in app.button if button.label == "Register"][0].click().run()
        return app

    def users(self):
        path = Path(self.folder.name, "users_db.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def test_a_new_username_is_registered(self):
        app = self.register("annie")
        self.assertEqual([item.value for item in app.exception], [])
        self.assertEqual(list(self.users()), ["annie"])

    def test_a_username_differing_only_in_case_is_refused(self):
        self.register("Annie")
        app = self.register("annie")
        self.assertEqual(list(self.users()), ["Annie"])
        self.assertEqual([item.value for item in app.error], ["User already exists"])

    def test_a_username_with_a_trailing_newline_is_refused(self):
        app = self.register("annie\n")
        self.assertEqual(self.users(), {})
        self.assertEqual(len(app.error), 1)

    def test_the_configured_admin_username_cannot_be_registered(self):
        app = self.register("Admin", admin={"username": "admin", "password": "s3cret-pass"})
        self.assertEqual(self.users(), {})
        self.assertEqual([item.value for item in app.error], ["User already exists"])


class ChangePasswordTest(AppFlowCase):
    LONG = "p" * 80

    def setUp(self):
        super().setUp()
        # The wrong-password delay is not what these tests check. Patch the app's backoff, never
        # time.sleep itself: Streamlit's script runner sleeps too and would spin until it times out.
        patcher = mock.patch("security.login_backoff_seconds", return_value=0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def users(self):
        return json.loads(Path(self.folder.name, "users_db.json").read_text(encoding="utf-8"))

    def legacy_user(self, password):
        self.write("users_db.json", json.dumps({"olduser": hashlib.sha256(password.encode()).hexdigest()}))
        return self.log_in("olduser", password)

    def change(self, app, current, new):
        app.text_input(key="pw_current").set_value(current)
        app.text_input(key="pw_new").set_value(new)
        app.button(key="btn_change_password").click().run()
        return app

    def info_texts(self, app):
        return [item.value for item in app.info]

    def test_an_account_still_on_a_legacy_hash_is_prompted_to_change_its_password(self):
        app = self.legacy_user(self.LONG)
        self.assertTrue(any("older, weaker" in text for text in self.info_texts(app)))

    def test_changing_the_password_replaces_the_legacy_hash_and_removes_the_prompt(self):
        app = self.legacy_user(self.LONG)
        self.change(app, self.LONG, "brand-new-pass1")
        self.assertEqual([item.value for item in app.exception], [])
        self.assertEqual([item.value for item in app.error], [])
        self.assertTrue(check_hashes("brand-new-pass1", self.users()["olduser"]))
        self.assertFalse(any("older, weaker" in text for text in self.info_texts(app)))
        again = self.log_in("olduser", "brand-new-pass1")
        self.assertTrue(again.session_state["logged_in"])

    def test_a_wrong_current_password_changes_nothing(self):
        app = self.legacy_user(self.LONG)
        before = self.users()
        self.change(app, "not-the-password", "brand-new-pass1")
        self.assertEqual(self.users(), before)
        self.assertEqual(len(app.error), 1)

    def test_a_new_password_that_breaks_the_rules_changes_nothing(self):
        app = self.legacy_user(self.LONG)
        before = self.users()
        for new in ("short", "x" * 73):
            self.change(app, self.LONG, new)
            self.assertEqual(self.users(), before, new)
            self.assertEqual(len(app.error), 1, new)

    def test_a_wrong_current_password_still_waits(self):
        app = self.legacy_user(self.LONG)
        with mock.patch("security.login_backoff_seconds", return_value=0) as backoff:
            self.change(app, "not-the-password", "brand-new-pass1")
        backoff.assert_called_once_with(1)

    def test_a_bcrypt_account_gets_the_form_but_no_prompt(self):
        self.write("users_db.json", json.dumps({"newuser": make_hashes("current-pass1")}))
        app = self.log_in("newuser", "current-pass1")
        self.assertEqual(len([w for w in app.text_input if w.key == "pw_current"]), 1)
        self.assertFalse(any("older, weaker" in text for text in self.info_texts(app)))
        self.change(app, "current-pass1", "another-pass22")
        self.assertTrue(check_hashes("another-pass22", self.users()["newuser"]))

    def test_the_admin_from_secrets_has_no_change_form(self):
        app = self.new_app()
        app.secrets["admin"] = {"username": "boss", "password": "secret-admin-pass"}
        app.run()
        app.text_input(key="login_user").set_value("boss")
        app.text_input(key="login_pass").set_value("secret-admin-pass")
        app.button[0].click().run()
        self.assertTrue(app.session_state["logged_in"])
        self.assertEqual([w for w in app.text_input if w.key == "pw_current"], [])


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

    def recovered_downloads(self, app):
        """The download buttons for set-aside files (the page has other download buttons too)."""
        return [item for item in app.get("download_button") if item.proto.label.startswith("personnel_db_")]

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

    def test_the_user_is_told_when_their_file_was_set_aside_and_can_download_it(self):
        app = self.open_page("5")
        [name] = self.quarantined()
        self.assertTrue(any(name in item.value for item in app.warning), [w.value for w in app.warning])
        self.assertEqual([item.proto.label for item in self.recovered_downloads(app)], [name])

    def test_no_notice_or_download_when_nothing_was_set_aside(self):
        app = self.open_page(json.dumps({"personnel": [PERSON]}))
        self.assertEqual([item.value for item in app.warning], [])
        self.assertEqual(self.recovered_downloads(app), [])

    def test_a_fixed_duty_target_of_the_wrong_type_does_not_crash_generate(self):
        record = dict(PERSON, fixed_duties_total="x", fixed_duties_weekend=None)
        app = self.open_page(json.dumps({"personnel": [record]}))
        [button for button in app.button if button.key == "btn_gen_schedule"][0].click().run()
        self.assertEqual([item.value for item in app.exception], [])

    def test_an_unknown_saved_language_falls_back_to_english(self):
        app = self.open_page(json.dumps({"personnel": [PERSON], "cfg_language": "French"}))
        self.assertEqual([item.value for item in app.exception], [])
        self.assertEqual(app.session_state["cfg_language"], "English")

    def test_the_language_choices_match_the_ones_a_saved_file_may_name(self):
        app = self.open_page(json.dumps({"personnel": [PERSON]}))
        self.assertEqual(list(app.selectbox(key="cfg_language").options), list(LANGUAGES))

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
