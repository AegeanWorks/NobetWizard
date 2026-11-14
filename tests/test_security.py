import hashlib
import unittest

from security import (
    check_hashes,
    login_backoff_seconds,
    make_hashes,
    secure_equals,
    verify_password,
)


class SecureEqualsTest(unittest.TestCase):
    def test_compares_ascii_and_unicode_text(self):
        self.assertTrue(secure_equals("şifre", "şifre"))
        self.assertFalse(secure_equals("şifre", "sifre"))
        self.assertTrue(secure_equals("plain", "plain"))

    def test_treats_missing_values_as_text(self):
        self.assertTrue(secure_equals(None, "None"))
        self.assertTrue(secure_equals(42, "42"))


class LoginBackoffTest(unittest.TestCase):
    def test_first_failure_waits_one_second(self):
        self.assertEqual(login_backoff_seconds(1), 1)

    def test_delay_grows_with_consecutive_failures(self):
        self.assertEqual(login_backoff_seconds(2), 2)
        self.assertEqual(login_backoff_seconds(3), 3)

    def test_delay_is_capped(self):
        self.assertEqual(login_backoff_seconds(9), 3)

    def test_non_positive_counter_is_minimum(self):
        self.assertEqual(login_backoff_seconds(0), 1)
        self.assertEqual(login_backoff_seconds(-4), 1)


class CheckHashesTest(unittest.TestCase):
    def test_rejects_missing_or_malformed_hashes(self):
        self.assertFalse(check_hashes("password", None))
        self.assertFalse(check_hashes("password", ""))
        self.assertFalse(check_hashes("password", "not-a-bcrypt-hash"))


class VerifyPasswordTest(unittest.TestCase):
    """Accounts created before the bcrypt switch store an unsalted SHA-256 hex digest."""

    def legacy(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def test_bcrypt_hash_matches_without_upgrade(self):
        self.assertEqual(verify_password("secret", make_hashes("secret")), (True, None))

    def test_legacy_hash_matches_and_returns_a_bcrypt_upgrade(self):
        matched, upgraded = verify_password("şifre", self.legacy("şifre"))
        self.assertTrue(matched)
        self.assertTrue(check_hashes("şifre", upgraded))

    def test_legacy_hash_is_case_insensitive_hex(self):
        matched, upgraded = verify_password("secret", self.legacy("secret").upper())
        self.assertTrue(matched)
        self.assertIsNotNone(upgraded)

    def test_wrong_password_never_upgrades(self):
        self.assertEqual(verify_password("wrong", self.legacy("secret")), (False, None))
        self.assertEqual(verify_password("wrong", make_hashes("secret")), (False, None))

    def test_missing_or_malformed_stored_values_fail(self):
        for stored in (None, "", 7, ["x"], "not-a-hash", "g" * 64, self.legacy("secret")[:-1]):
            self.assertEqual(verify_password("secret", stored), (False, None))

if __name__ == "__main__":
    unittest.main()
