# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document catalogues Python modules, classes, and exported functions. See Map Coverage for any stack it does not index.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `15`
- **Total Classes**: `33`
- **Total Top-Level Functions**: `51`
- **Total Class Methods**: `160`
- **Total Source Lines**: `3845`

## 🧭 Map Coverage
- **Indexed**: python (`15` module(s))
- **Not indexed by this map**: none (no non-Python source files were found)

---

## 📦 Modules & Exported Symbols

### [`exports.py`](exports.py)
> *Calendar export helpers that do not depend on the Streamlit UI.*

**Size**: `125` lines (`4421` bytes)

**Functions:**
- `def escape_ics_text(value)` - *Escape a value so it cannot break out of an iCalendar text property.*
- `def _fold_content_line(line, limit)` - *Split a content line so every physical line stays within the octet limit.*
- `def generate_ics(schedule, title)` - *Generate an iCalendar document for the schedule.*
- `def _file_sha256(path)`
- `def download_font(url, path, expected_sha256, timeout, max_bytes)` - *Fetch a font whose SHA-256 is known, without leaving a partial or unverified file.*

---

### [`main.py`](main.py)
**Size**: `1585` lines (`73384` bytes)

**Functions:**
- `def get_secrets()` - *Parse Streamlit secrets now; a missing or malformed file is a supported local configuration.*
- `def reserved_usernames()` - *Usernames that belong to the configured admin and cannot be registered by anyone else.*
- `def clear_user_state()` - *Drop every user-scoped key so the next login starts from a clean session.*
- `def clear_auth_state()` - *Drop the credentials and identity shown by the login page after logout.*
- `def get_firestore_db()` - *Initialize Firestore Client from Streamlit Secrets*
- `def get_user_db_path(username)`
- `def load_db(username)` - *Return (document, dropped): the saved state repaired in memory, and how many people were unusable.*
- `def save_db(personnel, username)`
- `def load_users()`
- `def save_users(data)`
- `def stored_password_hash(username)` - *The stored hash of a local or cloud account, or None for the secrets-only admin.*
- `def set_password_hash(username, old_hash, new_hash)` - *Store a new hash for a local or cloud account; False when it could not be written.*
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

**Size**: `92` lines (`3533` bytes)

**Functions:**
- `def secure_equals(left, right)` - *Compare two values in constant time, including non-ASCII text.*
- `def login_backoff_seconds(failures)` - *Seconds to pause after this many consecutive failed logins, capped at three.*
- `def make_hashes(password)` - *Hash a password with bcrypt.*
- `def check_hashes(password, hashed_text)` - *Return True only when the stored hash is a valid bcrypt hash matching the password.*
- `def password_problem(password)` - *Return the text key of the rule a new password breaks, or None when it is acceptable.*
- `def is_legacy_hash(stored)` - *True for an unsalted SHA-256 hex digest left from before the bcrypt switch.*
- `def is_valid_username(name)` - *A username is 3 to 20 ASCII letters, digits, dashes or underscores, with nothing after them.*
- `def username_taken(name, existing, reserved)` - *True when `name` matches an existing or reserved username ignoring case.*
- `def verify_password(password, stored)` - *Check a password against a stored hash and report whether the hash needs upgrading.*

---

### [`state_documents.py`](state_documents.py)
> *Shape checks for the saved personnel and users documents, free of UI dependencies.*

**Size**: `83` lines (`3344` bytes)

**Functions:**
- `def _is_int(value, low, high)`
- `def _usable_person(entry)` - *Return a repaired copy of a personnel entry, or None when it cannot be used.*
- `def normalize_personnel_document(data)` - *Return (document, dropped) for a loaded personnel document, or (None, 0) when unusable.*
- `def is_users_document(data)` - *The users file maps usernames to password hashes, so it must be an object.*

---

### [`storage.py`](storage.py)
**Size**: `109` lines (`4231` bytes)

**Functions:**
- `def _quarantine(target)` - *Move an unusable state file aside, never overwriting an earlier quarantined copy.*
- `def quarantined_copies(path)` - *The quarantined copies of one state file, newest first.*
- `def _quarantine_order(item)` - *Sort key from the `corrupt_<epoch>[_n]` suffix: a rename keeps the old modification time.*
- `def load_json_or_default(path, default, accept, on_quarantine)` - *Read a JSON document, quarantining an unreadable file instead of raising.*
- `def replace_json_entry(path, key, expected, new_value)` - *Set one top-level entry of a JSON object file, only while it still equals `expected`.*
- `def atomic_write_json(path, data)` - *Write JSON without leaving a truncated file when the process dies mid-write.*

---

### [`tests/__init__.py`](tests/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`tests/test_app_flows.py`](tests/test_app_flows.py)
> *End-to-end checks that drive main.py through Streamlit's AppTest in a throwaway folder.*

**Size**: `300` lines (`13678` bytes)

**Classes:**
- `class AppFlowCase` - *Runs each test inside its own temp folder so local state files never touch the repo.*
  - Method `.setUp()`
  - Method `.write(name, text)`
  - Method `.new_app()`
  - Method `.log_in(username, password)`
- `class LegacyLoginTest`
  - Method `.test_legacy_account_with_a_long_password_can_log_in()`
  - Method `.test_legacy_account_with_a_short_password_is_upgraded_to_bcrypt()`
- `class RegistrationTest`
  - Method `.register(username, password, admin)`
  - Method `.users()`
  - Method `.test_a_new_username_is_registered()`
  - Method `.test_a_username_differing_only_in_case_is_refused()`
  - Method `.test_a_username_with_a_trailing_newline_is_refused()`
  - Method `.test_the_configured_admin_username_cannot_be_registered()`
- `class ChangePasswordTest`
  - Method `.setUp()`
  - Method `.users()`
  - Method `.legacy_user(password)`
  - Method `.change(app, current, new)`
  - Method `.info_texts(app)`
  - Method `.test_an_account_still_on_a_legacy_hash_is_prompted_to_change_its_password()`
  - Method `.test_changing_the_password_replaces_the_legacy_hash_and_removes_the_prompt()`
  - Method `.test_a_wrong_current_password_changes_nothing()`
  - Method `.test_a_new_password_that_breaks_the_rules_changes_nothing()`
  - Method `.test_a_wrong_current_password_still_waits()`
  - Method `.test_a_bcrypt_account_gets_the_form_but_no_prompt()`
  - Method `.test_the_admin_from_secrets_has_no_change_form()`
- `class MalformedPersonnelStateTest`
  - Method `.open_page(raw)`
  - Method `.quarantined()`
  - Method `.recovered_downloads(app)` - *The download buttons for set-aside files (the page has other download buttons too).*
  - Method `.test_unusable_shapes_are_quarantined_and_the_page_loads()`
  - Method `.test_unusable_people_are_dropped_with_a_warning_and_the_file_is_kept()`
  - Method `.test_bad_settings_do_not_crash_the_page()`
  - Method `.test_the_user_is_told_when_their_file_was_set_aside_and_can_download_it()`
  - Method `.test_no_notice_or_download_when_nothing_was_set_aside()`
  - Method `.test_a_fixed_duty_target_of_the_wrong_type_does_not_crash_generate()`
  - Method `.test_an_unknown_saved_language_falls_back_to_english()`
  - Method `.test_the_language_choices_match_the_ones_a_saved_file_may_name()`
  - Method `.test_a_person_without_limits_gets_defaults()`
- `class MalformedUsersStateTest`
  - Method `.test_unusable_users_files_are_quarantined_and_login_fails_cleanly()`

**Functions:**
- `def _skip_component_scan()` - *Streamlit scans every installed package for v2 component manifests on each AppTest run.*
- `def _fast_bcrypt()` - *Hash with the minimum cost inside tests; the stored format and checks are unchanged.*

---

### [`tests/test_exports.py`](tests/test_exports.py)
**Size**: `161` lines (`6334` bytes)

**Classes:**
- `class IcsEscapingTest`
  - Method `.test_escapes_text_separators_and_newlines()`
  - Method `.test_generated_event_escapes_personnel_names()`
  - Method `.test_generated_events_carry_uid_and_dtstamp()`
  - Method `.test_generated_uid_is_stable_for_the_same_event()`
  - Method `.test_generated_ics_uses_crlf_and_folds_long_lines()`
- `class FakeResponse`
  - Method `.__init__(payload)`
  - Method `.__enter__()`
  - Method `.__exit__(*args)`
  - Method `.read(size)`
- `class DownloadFontTest`
  - Method `.download(folder, payload, expected, **options)`
  - Method `.test_existing_font_with_the_expected_hash_is_not_downloaded()`
  - Method `.test_existing_font_with_another_hash_is_replaced()`
  - Method `.test_download_uses_a_timeout_and_replaces_the_target()`
  - Method `.test_a_payload_with_another_hash_is_refused_and_leaves_nothing()`
  - Method `.test_a_payload_over_the_size_cap_is_refused_and_leaves_nothing()`
  - Method `.test_a_payload_exactly_at_the_cap_is_accepted()`
  - Method `.test_the_read_is_bounded_by_the_cap()`
- `class PinnedFontsTest`
  - Method `.test_fonts_are_pinned_to_a_commit_with_a_sha256()`
  - Method `.test_the_cap_leaves_room_for_the_real_fonts()`

**Functions:**
- `def sha256(payload)`

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
**Size**: `156` lines (`6534` bytes)

**Classes:**
- `class SecureEqualsTest`
  - Method `.test_compares_ascii_and_unicode_text()`
  - Method `.test_treats_missing_values_as_text()`
- `class LoginBackoffTest`
  - Method `.test_first_failure_waits_one_second()`
  - Method `.test_delay_grows_with_consecutive_failures()`
  - Method `.test_delay_is_capped()`
  - Method `.test_non_positive_counter_is_minimum()`
- `class PasswordRulesTest`
  - Method `.test_a_password_of_8_characters_up_to_72_bytes_has_no_problem()`
  - Method `.test_too_short_and_too_long_passwords_name_their_problem()`
  - Method `.test_non_text_is_a_problem()`
- `class ProductionCostTest`
  - Method `.test_real_hashes_use_bcrypts_default_cost()`
- `class LegacyHashTest`
  - Method `.test_a_sha256_hex_digest_is_legacy_and_a_bcrypt_hash_is_not()`
- `class UsernameTest`
  - Method `.test_valid_usernames_are_3_to_20_letters_digits_dash_or_underscore()`
  - Method `.test_invalid_usernames_are_rejected_including_a_trailing_newline()`
  - Method `.test_a_name_is_taken_when_it_matches_ignoring_case()`
  - Method `.test_reserved_names_are_taken_too()`
  - Method `.test_non_text_entries_do_not_break_the_comparison()`
- `class CheckHashesTest`
  - Method `.test_rejects_missing_or_malformed_hashes()`
- `class VerifyPasswordTest` - *Accounts created before the bcrypt switch store an unsalted SHA-256 hex digest.*
  - Method `.setUp()`
  - Method `.legacy(password)`
  - Method `.test_bcrypt_hash_matches_without_upgrade()`
  - Method `.test_legacy_hash_matches_and_returns_a_bcrypt_upgrade()`
  - Method `.test_legacy_hash_is_case_insensitive_hex()`
  - Method `.test_wrong_password_never_upgrades()`
  - Method `.test_legacy_password_over_72_bytes_logs_in_without_an_upgrade()`
  - Method `.test_legacy_password_of_exactly_72_bytes_is_upgraded()`
  - Method `.test_wrong_long_password_still_fails()`
  - Method `.test_missing_or_malformed_stored_values_fail()`

---

### [`tests/test_state_documents.py`](tests/test_state_documents.py)
**Size**: `112` lines (`5591` bytes)

**Classes:**
- `class NormalizePersonnelDocumentTest`
  - Method `.test_a_saved_document_passes_through_unchanged()`
  - Method `.test_a_bare_list_is_the_legacy_personnel_format()`
  - Method `.test_unusable_top_level_shapes_return_none()`
  - Method `.test_an_empty_object_or_list_is_an_empty_roster()`
  - Method `.test_entries_that_are_not_usable_people_are_dropped_and_counted()`
  - Method `.test_missing_limits_get_the_add_form_defaults()`
  - Method `.test_limits_of_the_wrong_type_get_the_defaults()`
  - Method `.test_settings_of_the_wrong_type_or_range_are_dropped()`
  - Method `.test_unknown_keys_are_kept()`
  - Method `.test_fixed_duty_targets_of_the_wrong_type_become_zero()`
  - Method `.test_a_missing_fixed_duty_target_is_left_for_the_app_to_default()`
  - Method `.test_only_known_languages_are_kept()`
  - Method `.test_the_input_is_not_modified()`
- `class IsUsersDocumentTest`
  - Method `.test_only_an_object_is_a_users_document()`

**Functions:**
- `def person(**overrides)`

---

### [`tests/test_storage.py`](tests/test_storage.py)
**Size**: `214` lines (`10043` bytes)

**Classes:**
- `class LoadJsonOrDefaultTest`
  - Method `.test_reads_an_existing_document()`
  - Method `.test_missing_file_returns_the_default()`
  - Method `.test_corrupt_file_is_quarantined_and_default_returned()`
- `class AtomicWriteJsonTest`
  - Method `.test_writes_and_overwrites_json()`
  - Method `.test_leaves_no_temporary_files()`
  - Method `.test_creates_missing_parent_directory()`
- `class AcceptTest`
  - Method `.test_a_document_the_check_rejects_is_quarantined_like_a_corrupt_one()`
  - Method `.test_a_document_the_check_accepts_is_returned_and_kept()`
  - Method `.test_the_default_is_not_checked()`
- `class QuarantineReportTest`
  - Method `.test_on_quarantine_receives_the_new_path_for_corrupt_and_rejected_files()`
  - Method `.test_on_quarantine_is_not_called_for_a_good_or_missing_file()`
- `class QuarantineRetentionTest`
  - Method `.corrupt_and_load(path, stamp, label)`
  - Method `.test_only_the_newest_copies_are_kept()`
  - Method `.test_pruning_never_touches_other_files_or_the_live_file()`
  - Method `.test_the_copy_just_made_is_never_the_one_pruned()`
- `class QuarantinedCopiesTest`
  - Method `.test_lists_only_this_files_copies_newest_first()`
  - Method `.test_a_missing_folder_has_no_copies()`
- `class QuarantineCollisionTest`
  - Method `.test_two_corrupt_files_in_the_same_second_are_both_kept()`
- `class ReplaceJsonEntryTest`
  - Method `.test_replaces_only_the_named_entry_when_it_is_unchanged()`
  - Method `.test_keeps_an_entry_added_after_the_caller_read_the_file()`
  - Method `.test_leaves_the_file_alone_when_the_entry_changed_or_is_missing()`

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
