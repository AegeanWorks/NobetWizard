# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document catalogues Python modules, classes, and exported functions. See Map Coverage for any stack it does not index.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `12`
- **Total Classes**: `12`
- **Total Top-Level Functions**: `30`
- **Total Class Methods**: `62`
- **Total Source Lines**: `2742`

## 🧭 Map Coverage
- **Indexed**: python (`12` module(s))
- **Not indexed by this map**: none (no non-Python source files were found)

---

## 📦 Modules & Exported Symbols

### [`exports.py`](exports.py)
> *Calendar export helpers that do not depend on the Streamlit UI.*

**Size**: `93` lines (`2999` bytes)

**Functions:**
- `def escape_ics_text(value)` - *Escape a value so it cannot break out of an iCalendar text property.*
- `def _fold_content_line(line, limit)` - *Split a content line so every physical line stays within the octet limit.*
- `def generate_ics(schedule, title)` - *Generate an iCalendar document for the schedule.*
- `def download_font(url, path, timeout)` - *Download a font once, with a timeout and without leaving a partial file.*

---

### [`main.py`](main.py)
**Size**: `1457` lines (`66497` bytes)

**Functions:**
- `def get_secrets()` - *st.secrets raises when no secrets file exists; an empty mapping keeps local runs working.*
- `def clear_user_state()` - *Drop every user-scoped key so the next login starts from a clean session.*
- `def clear_auth_state()` - *Drop the credentials and identity shown by the login page after logout.*
- `def get_firestore_db()` - *Initialize Firestore Client from Streamlit Secrets*
- `def get_user_db_path(username)`
- `def load_db(username)`
- `def save_db(personnel, username)`
- `def load_users()`
- `def save_users(data)`
- `def authenticate(username, password)`
- `def login_page()`
- `def generate_excel(df_res)`
- `def generate_pdf(df_res, year, month, t)`
- `def main()`

---

### [`scheduler.py`](scheduler.py)
**Size**: `477` lines (`21092` bytes)

**Classes:**
- `class DutyScheduler`
  - Method `.__init__(year, month, personnel_list, config)` - *personnel_list: list of dicts [{'name': '...', 'gender': 'M/F', 'max_duties': 5, 'max_weekends': 2}]*
  - Method `.is_weekend(d)`
  - Method `.get_week_number(d)`
  - Method `._split_dates(person, field)`
  - Method `._is_fixed_on(person_name, d)`
  - Method `._duties_in_week(person_name, week)`
  - Method `._reset_counters()`
  - Method `._increment_fixed(person, d)`
  - Method `._restore_baseline()`
  - Method `._index_fixed_duties()`
  - Method `._validate_fixed_duties()` - *Commit every fixed duty first: a fixed duty that breaks availability, rest,*
  - Method `.check_constraints(person, current_date, current_team)`
  - Method `.check_team_constraints(team)`
  - Method `.generate()`

---

### [`security.py`](security.py)
> *Password and credential helpers kept free of UI dependencies.*

**Size**: `36` lines (`1076` bytes)

**Functions:**
- `def secure_equals(left, right)` - *Compare two values in constant time, including non-ASCII text.*
- `def login_backoff_seconds(failures)` - *Seconds to pause after this many consecutive failed logins, capped at three.*
- `def make_hashes(password)` - *Hash a password with bcrypt.*
- `def check_hashes(password, hashed_text)` - *Return True only when the stored hash is a valid bcrypt hash matching the password.*

---

### [`storage.py`](storage.py)
**Size**: `49` lines (`1722` bytes)

**Functions:**
- `def load_json_or_default(path, default)` - *Read a JSON document, quarantining an unreadable file instead of raising.*
- `def atomic_write_json(path, data)` - *Write JSON without leaving a truncated file when the process dies mid-write.*

---

### [`tests/__init__.py`](tests/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`tests/test_exports.py`](tests/test_exports.py)
**Size**: `95` lines (`3540` bytes)

**Classes:**
- `class IcsEscapingTest`
  - Method `.test_escapes_text_separators_and_newlines()`
  - Method `.test_generated_event_escapes_personnel_names()`
  - Method `.test_generated_events_carry_uid_and_dtstamp()`
  - Method `.test_generated_uid_is_stable_for_the_same_event()`
  - Method `.test_generated_ics_uses_crlf_and_folds_long_lines()`
- `class DownloadFontTest`
  - Method `.test_existing_font_is_not_downloaded()`
  - Method `.test_download_uses_a_timeout_and_replaces_the_target()`

---

### [`tests/test_scheduler.py`](tests/test_scheduler.py)
**Size**: `255` lines (`8834` bytes)

**Classes:**
- `class DutySchedulerTest`
  - Method `.test_generate_fills_every_day_without_consecutive_duties()`
  - Method `.test_fixed_duty_is_assigned_on_its_date()`
  - Method `.test_busy_weekday_blocks_assignment()`
  - Method `.test_holiday_counts_as_weekend()`
  - Method `.test_two_day_rest_applies_even_when_consecutive_is_allowed()`
  - Method `.test_mixed_gender_allows_single_person_days()`
  - Method `.test_conditional_rule_uses_previous_week_trigger()`
  - Method `.test_fixed_duty_on_leave_is_reported()`
  - Method `.test_fixed_duties_cannot_exceed_people_per_day()`
  - Method `.test_fixed_duties_cannot_pair_incompatible_people()`
  - Method `.test_fixed_duties_cannot_exceed_max_duties()`
  - Method `.test_empty_personnel_name_is_rejected()`
  - Method `.test_fixed_validation_failure_restores_clean_counters()`
  - Method `.test_duplicate_personnel_names_are_rejected()`
  - Method `.test_same_day_conditional_rule_is_rejected()`
  - Method `.test_failed_search_restores_fixed_baseline_counts()`
  - Method `.test_failed_search_clears_partial_schedule()`
  - Method `.test_list_format_constraints_block_assignment()`

**Functions:**
- `def personnel(count)`
- `def config(**overrides)`

---

### [`tests/test_security.py`](tests/test_security.py)
**Size**: `41` lines (`1417` bytes)

**Classes:**
- `class SecureEqualsTest`
  - Method `.test_compares_ascii_and_unicode_text()`
  - Method `.test_treats_missing_values_as_text()`
- `class LoginBackoffTest`
  - Method `.test_first_failure_waits_one_second()`
  - Method `.test_delay_grows_with_consecutive_failures()`
  - Method `.test_delay_is_capped()`
  - Method `.test_non_positive_counter_is_minimum()`
- `class CheckHashesTest`
  - Method `.test_rejects_missing_or_malformed_hashes()`

---

### [`tests/test_storage.py`](tests/test_storage.py)
**Size**: `63` lines (`2446` bytes)

**Classes:**
- `class LoadJsonOrDefaultTest`
  - Method `.test_reads_an_existing_document()`
  - Method `.test_missing_file_returns_the_default()`
  - Method `.test_corrupt_file_is_quarantined_and_default_returned()`
- `class AtomicWriteJsonTest`
  - Method `.test_writes_and_overwrites_json()`
  - Method `.test_leaves_no_temporary_files()`
  - Method `.test_creates_missing_parent_directory()`

---

### [`tests/test_ui_helpers.py`](tests/test_ui_helpers.py)
**Size**: `82` lines (`3136` bytes)

**Classes:**
- `class GenderModeTest`
  - Method `.test_internal_modes_are_unchanged()`
  - Method `.test_legacy_localized_labels_normalize()`
  - Method `.test_unknown_value_falls_back_to_any()`
  - Method `.test_label_follows_the_selected_language()`
- `class CalendarTitleTest`
  - Method `.test_english_title_drops_the_emoji_and_parenthetical()`
  - Method `.test_turkish_title_drops_the_emoji()`
  - Method `.test_empty_or_emoji_only_title_falls_back()`
- `class CalendarHtmlTest`
  - Method `.test_personnel_names_are_html_escaped()`
  - Method `.test_empty_cells_and_assignments_still_render()`
  - Method `.test_holiday_weekday_renders_with_weekend_shading()`

---

### [`ui_helpers.py`](ui_helpers.py)
> *Pure presentation helpers shared by the Streamlit UI and the test suite.*

**Size**: `94` lines (`3513` bytes)

**Functions:**
- `def gender_label(options, mode)` - *Return the localized label for an internal gender mode.*
- `def normalize_gender_mode(value, option_sets)` - *Accept an internal mode or a legacy localized label from saved data.*
- `def calendar_title(app_title, month, year)` - *A readable title for an exported calendar: the app name plus the roster month.*
- `def get_calendar_html(year, month, schedule, t, holidays)` - *Render the month grid, escaping every personnel name it embeds.*

---
