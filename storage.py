import json
import os
import tempfile
import time
from pathlib import Path


def _quarantine(target):
    """Move an unusable state file aside, never overwriting an earlier quarantined copy."""
    stamp = int(time.time())
    quarantine = target.with_name(f"{target.name}.corrupt_{stamp}")
    suffix = 1
    while quarantine.exists():  # a second corruption in the same second must not overwrite the first
        quarantine = target.with_name(f"{target.name}.corrupt_{stamp}_{suffix}")
        suffix += 1
    try:
        os.replace(target, quarantine)
    except OSError:  # hygiene: allow best-effort quarantine; the unusable state still falls back
        pass


def load_json_or_default(path, default, accept=None):
    """Read a JSON document, quarantining an unreadable file instead of raising.

    A truncated or hand-edited state file must not lock the user out of the app, and the
    damaged bytes are kept next to it for inspection rather than deleted. `accept`, when given,
    is called with the parsed document; a document it rejects is set aside exactly like a corrupt
    one, so a valid-JSON file of the wrong shape cannot reach the caller.
    """
    target = Path(path)
    if not target.exists():
        return default
    try:
        with open(target, "r", encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        _quarantine(target)
        return default
    if accept is not None and not accept(document):
        _quarantine(target)
        return default
    return document


def replace_json_entry(path, key, expected, new_value):
    """Set one top-level entry of a JSON object file, only while it still equals `expected`.

    The file is re-read right before the write so entries added since the caller last read it
    are kept. Returns True when the entry was replaced.
    """
    document = load_json_or_default(path, {})
    if not isinstance(document, dict) or document.get(key) != expected:
        return False
    document[key] = new_value
    atomic_write_json(path, document)
    return True


def atomic_write_json(path, data):
    """Write JSON without leaving a truncated file when the process dies mid-write."""
    target = Path(path)
    directory = target.parent if str(target.parent) else Path(".")
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(directory)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=4)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:  # hygiene: allow best-effort cleanup of the temp file after a failed write
            pass
        raise
    return target
