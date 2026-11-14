"""Calendar export helpers that do not depend on the Streamlit UI."""

import hashlib
import os
import urllib.request
from datetime import datetime, timedelta, timezone


def escape_ics_text(value):
    """Escape a value so it cannot break out of an iCalendar text property."""
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
    )


def _fold_content_line(line, limit=75):
    """Split a content line so every physical line stays within the octet limit."""
    if len(line.encode("utf-8")) <= limit:
        return [line]
    chunks = []
    current = ""
    for character in line:
        if len((current + character).encode("utf-8")) > limit:
            chunks.append(current)
            current = " " + character
        else:
            current += character
    chunks.append(current)
    return chunks


def generate_ics(schedule, title="Duty Roster"):
    """Generate an iCalendar document for the schedule."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NobetWizard//DutyRoster//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for day, team in schedule.items():
        names = escape_ics_text(", ".join([person["name"] for person in team]))
        dt_start = day.strftime("%Y%m%d")
        dt_end = (day + timedelta(days=1)).strftime("%Y%m%d")
        uid_seed = f"{dt_start}:{names}".encode("utf-8")
        uid = hashlib.sha256(uid_seed).hexdigest()[:32] + "@nobetwizard"

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{uid}")
        lines.append(f"DTSTAMP:{stamp}")
        lines.append(f"DTSTART;VALUE=DATE:{dt_start}")
        lines.append(f"DTEND;VALUE=DATE:{dt_end}")
        lines.append(f"SUMMARY:{escape_ics_text(title)}: {names}")
        lines.append(f"DESCRIPTION:Team: {names}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    folded = []
    for line in lines:
        folded.extend(_fold_content_line(line))
    return ("\r\n".join(folded) + "\r\n").encode("utf-8")


FONT_MAX_BYTES = 2 * 1024 * 1024  # the real Roboto files are about 0.5 MB
# Pinned to a commit of the Roboto sources, not to a branch, with the SHA-256 of each file.
_ROBOTO_BASE = (
    "https://raw.githubusercontent.com/googlefonts/roboto-2/"
    "eaef3058ec9d4f426c013b29fae53345e1c36f67/src/hinted/"
)
ROBOTO_REGULAR = (
    _ROBOTO_BASE + "Roboto-Regular.ttf",
    "56a45233d29f11b4dfb86d248e921939d115778f87325e7ae8cc108383d6664d",
)
ROBOTO_BOLD = (
    _ROBOTO_BASE + "Roboto-Bold.ttf",
    "61f89f8db49261c2f6106e8dccc35df7b2f7ed909020db40a3fc905e95f99334",
)


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def download_font(url, path, expected_sha256, timeout=10, max_bytes=FONT_MAX_BYTES):
    """Fetch a font whose SHA-256 is known, without leaving a partial or unverified file.

    A file already at `path` with the expected hash is kept; one with another hash is replaced.
    The response is read up to `max_bytes` plus one byte, and a larger or differently hashed
    payload raises ValueError before anything is written under the final name.
    """
    import tempfile

    target = os.fspath(path)
    if os.path.exists(target) and _file_sha256(target) == expected_sha256:
        return

    directory = os.path.dirname(target) or "."
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{os.path.basename(target)}.", suffix=".tmp", dir=directory
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise ValueError(f"font download exceeds {max_bytes} bytes")
            if hashlib.sha256(payload).hexdigest() != expected_sha256:
                raise ValueError("font download does not match the expected SHA-256")
            handle.write(payload)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
