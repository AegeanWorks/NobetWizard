"""Password and credential helpers kept free of UI dependencies."""

import hashlib
import hmac
import re


BCRYPT_HASH = re.compile(r"^\$2[abxy]?\$\d{2}\$[./A-Za-z0-9]{53}$")


def secure_equals(left, right):
    """Compare two values in constant time, including non-ASCII text."""
    return hmac.compare_digest(str(left).encode("utf-8"), str(right).encode("utf-8"))


def login_backoff_seconds(failures):
    """Seconds to pause after this many consecutive failed logins, capped at three."""
    return min(3, max(1, int(failures)))


def make_hashes(password):
    """Hash a password with bcrypt."""
    import bcrypt

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_hashes(password, hashed_text):
    """Return True only when the stored hash is a valid bcrypt hash matching the password."""
    if not isinstance(hashed_text, str) or not BCRYPT_HASH.match(hashed_text):
        return False
    try:
        import bcrypt

        return bcrypt.checkpw(password.encode(), hashed_text.encode())
    except (ValueError, TypeError):
        return False


LEGACY_SHA256_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
BCRYPT_MAX_BYTES = 72
USERNAME_PATTERN = re.compile(r"[a-zA-Z0-9_-]{3,20}")
MIN_PASSWORD_CHARACTERS = 8


def password_problem(password):
    """Return the text key of the rule a new password breaks, or None when it is acceptable."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_CHARACTERS:
        return "err_password_short"
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        return "err_password_long"
    return None


def is_legacy_hash(stored):
    """True for an unsalted SHA-256 hex digest left from before the bcrypt switch."""
    return isinstance(stored, str) and LEGACY_SHA256_HASH.match(stored) is not None


def is_valid_username(name):
    """A username is 3 to 20 ASCII letters, digits, dashes or underscores, with nothing after them."""
    return isinstance(name, str) and USERNAME_PATTERN.fullmatch(name) is not None


def username_taken(name, existing, reserved=()):
    """True when `name` matches an existing or reserved username ignoring case.

    Per-user files are named from the username, and Windows and macOS treat names that differ only
    in case as the same file, so such names would share one person's saved data.
    """
    folded = str(name).casefold()
    return any(str(other).casefold() == folded for other in (*existing, *reserved) if isinstance(other, str))


def verify_password(password, stored):
    """Check a password against a stored hash and report whether the hash needs upgrading.

    Returns (matched, upgraded_hash). Accounts created before the bcrypt switch hold an
    unsalted SHA-256 hex digest; a correct password for one returns a fresh bcrypt hash so the
    caller can replace it. A wrong password or an unreadable stored value never upgrades, and a
    password over bcrypt's 72-byte limit logs in but keeps its legacy hash.
    """
    if check_hashes(password, stored):
        return True, None
    if isinstance(stored, str) and LEGACY_SHA256_HASH.match(stored):
        encoded = str(password).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        if hmac.compare_digest(digest.encode("ascii"), stored.lower().encode("ascii")):
            if len(encoded) > BCRYPT_MAX_BYTES:
                return True, None  # bcrypt cannot hash this; keep the legacy hash rather than fail the login
            return True, make_hashes(password)
    return False, None
