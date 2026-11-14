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
