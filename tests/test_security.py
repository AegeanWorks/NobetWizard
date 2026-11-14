import unittest

from security import check_hashes, login_backoff_seconds, secure_equals


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


if __name__ == "__main__":
    unittest.main()
