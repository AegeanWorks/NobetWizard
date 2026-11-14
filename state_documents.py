"""Shape checks for the saved personnel and users documents, free of UI dependencies.

A state file or cloud document can parse as JSON and still hold values the app cannot use
(a number, a null roster, a person without a gender). These helpers decide what is unusable
as a whole and repair the rest in memory, so a bad value never reaches the page.
"""
import copy

DEFAULT_MAX_DUTIES = 5  # the add-person form defaults
DEFAULT_MAX_WEEKENDS = 2
GENDERS = ("M", "F")


def _is_int(value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return (low is None or value >= low) and (high is None or value <= high)


SETTING_CHECKS = {
    "conditional_rules": lambda v: isinstance(v, list),
    "forbidden_pairs": lambda v: isinstance(v, list),
    "holidays_multiselect": lambda v: isinstance(v, list),
    "cfg_year": lambda v: _is_int(v, 1900, 2200),
    "cfg_month": lambda v: _is_int(v, 1, 12),
    "cfg_ppl": lambda v: _is_int(v, 1),
    "cfg_min_seniors": lambda v: _is_int(v, 0),
    "cfg_max_weekly": lambda v: _is_int(v, 0),
    "cfg_consecutive": lambda v: isinstance(v, bool),
    "cfg_two_rest": lambda v: isinstance(v, bool),
    "cfg_gender": lambda v: isinstance(v, str),
    "cfg_language": lambda v: isinstance(v, str),
}


def _usable_person(entry):
    """Return a repaired copy of a personnel entry, or None when it cannot be used."""
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    if not isinstance(name, str) or not name.strip() or entry.get("gender") not in GENDERS:
        return None
    person = dict(entry)
    if not _is_int(person.get("max_duties"), 0):
        person["max_duties"] = DEFAULT_MAX_DUTIES
    if not _is_int(person.get("max_weekends"), 0):
        person["max_weekends"] = DEFAULT_MAX_WEEKENDS
    return person


def normalize_personnel_document(data):
    """Return (document, dropped) for a loaded personnel document, or (None, 0) when unusable.

    None means the whole document has the wrong shape and should be set aside. Otherwise the
    people that cannot be used are dropped (and counted) and the saved settings of the wrong type
    are discarded; the input is never modified and unknown keys are kept.
    """
    if isinstance(data, list):
        data = {"personnel": data}
    if not isinstance(data, dict):
        return None, 0
    people = data.get("personnel", [])
    if not isinstance(people, list):
        return None, 0
    document = {}
    for key, value in data.items():
        if key == "personnel":
            continue
        check = SETTING_CHECKS.get(key)
        if check is None or check(value):
            document[key] = copy.deepcopy(value)
    kept = [person for person in map(_usable_person, people) if person is not None]
    document = {"personnel": kept, **document}
    return document, len(people) - len(kept)


def is_users_document(data):
    """The users file maps usernames to password hashes, so it must be an object."""
    return isinstance(data, dict)
