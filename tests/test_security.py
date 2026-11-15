import hashlib
import unittest

from security import (
    check_hashes,
    is_legacy_hash,
    is_valid_username,
    login_backoff_seconds,
    make_hashes,
    password_problem,
    secure_equals,
    username_taken,
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


class PasswordRulesTest(unittest.TestCase):
    def test_a_password_of_8_characters_up_to_72_bytes_has_no_problem(self):
        for password in ("12345678", "x" * 72, "ş" * 36):
            self.assertIsNone(password_problem(password), password)

    def test_too_short_and_too_long_passwords_name_their_problem(self):
        self.assertEqual(password_problem("1234567"), "err_password_short")
        self.assertEqual(password_problem(""), "err_password_short")
        self.assertEqual(password_problem("x" * 73), "err_password_long")
        self.assertEqual(password_problem("ş" * 37), "err_password_long")

    def test_non_text_is_a_problem(self):
        self.assertEqual(password_problem(None), "err_password_short")


class LegacyHashTest(unittest.TestCase):
    def test_a_sha256_hex_digest_is_legacy_and_a_bcrypt_hash_is_not(self):
        self.assertTrue(is_legacy_hash(hashlib.sha256(b"x").hexdigest()))
        self.assertTrue(is_legacy_hash(hashlib.sha256(b"x").hexdigest().upper()))
        self.assertFalse(is_legacy_hash(make_hashes("secret-pass")))
        for value in (None, "", 5, "g" * 64, "a" * 63):
            self.assertFalse(is_legacy_hash(value), repr(value))


class UsernameTest(unittest.TestCase):
    def test_valid_usernames_are_3_to_20_letters_digits_dash_or_underscore(self):
        for name in ("abc", "Ann_1", "a-b", "x" * 20):
            self.assertTrue(is_valid_username(name), name)

    def test_invalid_usernames_are_rejected_including_a_trailing_newline(self):
        for name in ("ab", "x" * 21, "has space", "dot.name", "abc\n", "ş" * 4, "", None, 7):
            self.assertFalse(is_valid_username(name), repr(name))

    def test_a_name_is_taken_when_it_matches_ignoring_case(self):
        self.assertTrue(username_taken("ann", ["Ann", "bob"]))
        self.assertTrue(username_taken("BOB", {"Ann": "h", "bob": "h"}))
        self.assertFalse(username_taken("cem", ["Ann", "bob"]))

    def test_reserved_names_are_taken_too(self):
        self.assertTrue(username_taken("Admin", [], reserved=["admin"]))
        self.assertFalse(username_taken("user", [], reserved=["admin"]))

    def test_non_text_entries_do_not_break_the_comparison(self):
        self.assertFalse(username_taken("ann", [None, 5]))


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

    def test_legacy_password_over_72_bytes_logs_in_without_an_upgrade(self):
        # bcrypt cannot hash more than 72 bytes; the legacy hash stays and the login still works.
        for password in ("p" * 80, "ş" * 37):
            self.assertEqual(verify_password(password, self.legacy(password)), (True, None))

    def test_legacy_password_of_exactly_72_bytes_is_upgraded(self):
        password = "ş" * 36
        self.assertEqual(len(password.encode("utf-8")), 72)
        matched, upgraded = verify_password(password, self.legacy(password))
        self.assertTrue(matched)
        self.assertTrue(check_hashes(password, upgraded))

    def test_wrong_long_password_still_fails(self):
        self.assertEqual(verify_password("q" * 80, self.legacy("p" * 80)), (False, None))

    def test_missing_or_malformed_stored_values_fail(self):
        for stored in (None, "", 7, ["x"], "not-a-hash", "g" * 64, self.legacy("secret")[:-1]):
            self.assertEqual(verify_password("secret", stored), (False, None))

if __name__ == "__main__":
    unittest.main()
