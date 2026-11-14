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


def download_font(url, path, timeout=10):
    """Download a font once, with a timeout and without leaving a partial file."""
    import tempfile

    target = os.fspath(path)
    if os.path.exists(target):
        return

    directory = os.path.dirname(target) or "."
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{os.path.basename(target)}.", suffix=".tmp", dir=directory
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                handle.write(response.read())
        if os.path.exists(target):
            return
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
