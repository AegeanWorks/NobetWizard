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


def generate_ics(schedule, title="Duty Roster"):
    """Generate an iCalendar document for the schedule."""
    ics_content = [
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

        ics_content.append("BEGIN:VEVENT")
        ics_content.append(f"UID:{uid}")
        ics_content.append(f"DTSTAMP:{stamp}")
        ics_content.append(f"DTSTART;VALUE=DATE:{dt_start}")
        ics_content.append(f"DTEND;VALUE=DATE:{dt_end}")
        ics_content.append(f"SUMMARY:{escape_ics_text(title)}: {names}")
        ics_content.append(f"DESCRIPTION:Team: {names}")
        ics_content.append("END:VEVENT")

    ics_content.append("END:VCALENDAR")
    return "\n".join(ics_content).encode("utf-8")


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
