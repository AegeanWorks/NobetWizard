import json
import os
import tempfile
import time
from pathlib import Path


def load_json_or_default(path, default):
    """Read a JSON document, quarantining an unreadable file instead of raising.

    A truncated or hand-edited state file must not lock the user out of the app, and the
    damaged bytes are kept next to it for inspection rather than deleted.
    """
    target = Path(path)
    if not target.exists():
        return default
    try:
        with open(target, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        quarantine = target.with_name(f"{target.name}.corrupt_{int(time.time())}")
        try:
            os.replace(target, quarantine)
        except OSError:  # hygiene: allow best-effort quarantine; the unreadable state still falls back
            pass
        return default


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
