# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Store the gender rule as a language-independent token
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The selected gender rule was saved as its localized display label, so changing the UI language could leave saved data that no longer matched the current options.
- **Decision**: Persist `Any`, `Mixed` or `Single Gender`; translate only at render time and normalize legacy localized labels when loading.
- **Consequences**: New saves are language-independent, old files remain readable, and the selectbox no longer stores display text.

### ADR-002: Keep UI and security helpers in pure modules
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The Streamlit entry point mixes pure presentation logic, password checks and UI orchestration, which made the former two impossible to test without the full UI dependency set.
- **Decision**: Move language labels, calendar markup, password hashing and constant-time comparison into `ui_helpers.py` and `security.py`.
- **Consequences**: These helpers are unit-testable with the standard library, while `main.py` keeps only orchestration and Streamlit-specific code.

### ADR-003: Escape iCalendar text and time-box font downloads
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: Personnel names were interpolated into iCalendar properties without escaping, so commas, semicolons or newlines could corrupt or inject events; PDF font downloads had no timeout and could leave partial files.
- **Decision**: Escape every iCalendar text value and download each font once through a 10-second timeout into a temporary file before replacing the target.
- **Consequences**: Exported calendars stay well-formed for any name, and PDF generation fails over to built-in fonts instead of hanging on a slow network.

### ADR-004: Login gate keeper; ui_kind corrected to web; roster deferred past auth
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: No screenshots existed and `media.json` mislabeled the Streamlit app as `desktop`; the roster needs credentials (super-admin fallback is secrets-gated) and headless `--screenshot` cannot hydrate Streamlit.
- **Decision**: Correct `ui_kind` to `web`; register `2026-11-03-app.png` (Playwright capture of `streamlit run main.py` login, commit `f8b591d`, viewport 1440x900) in `.aikit/media.json` and the README `aegean:screenshots` block. Roster views wait for an authenticated session. Installed missing declared deps (reportlab, pandas, holidays) to run the app.
- **Consequences**: README proves the real login gate. Reproduce with: install requirements, `streamlit run main.py`, Playwright screenshot after network idle plus settle wait.

### ADR-005: Enforce web ui_kind via manual ui-id after detector drift
- **Date**: 2026-11-03
- **Status**: Accepted
- **Context**: ADR-004 corrected `ui_kind` to `web` in `media.json`, but `aikit ui-id` still detected `desktop` from `requirements.txt` and `project.json` kept `ui_kind: desktop` with `ui_source: detected` (2026-10-28), contradicting the Streamlit web app (`streamlit run main.py`).
- **Decision**: Run `python aikit.py ui-id NobetWizard --set yes --kind web`; `project.json` now records `ui_kind: web` with `ui_source: manual` (2026-11-03), matching `media.json`.
- **Consequences**: Catalog display and media pipeline agree the app is web; detector evidence stays `requirements.txt` (minimal change); re-detection with `--set auto` would regress to desktop and must not be used without updating evidence to `main.py`.

### ADR-006: Harden scheduler guards, UI validation and calendar exports
- **Date**: 2026-11-06
- **Status**: Accepted
- **Context**: The verify-3push audit found duplicate personnel names silently corrupting name-matched scheduling, failed searches leaking partial duty counters into the editor, list-typed constraints crashing string splits, same-day conditional rules accepted by the UI, single-day leave rejected by the bulk tool, holidays shown as weekdays while counted as weekends, iCalendar events missing UID/DTSTAMP, help text quoting the wrong date format, editor merges matched by position, and a shared font-download temp path.
- **Decision**: Reject duplicate names and same-day rules in `generate()` with clear errors; restore the fixed baseline before returning failure; parse busy/off/leave through `_split_dates`; guard the add-person form (strip, reject empty/duplicates) and the rule form; accept single-day bulk leave; shade holidays as weekends in the calendar and list views; emit stable UID plus DTSTAMP per event; correct help text to DD/MM/YYYY; merge editor rows by name; download fonts through unique temp files; drop unused CSV/template/header keys.
- **Consequences**: Invalid rosters fail fast with actionable messages instead of silent mismatch; the UI no longer shows partial counts or accepts meaningless rules; exports deduplicate on re-import; holiday display matches scheduler counting; 7 new regression tests pin the behavior (34 total).

### ADR-007: Reject empty names, clean counters on invalid fixed duties, and scope tool widgets per person
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: A blank name from the free-form personnel editor could be scheduled as an unnamed roster entry; a failed fixed-duty validation returned after reserving some duties, leaving partial counters in the personnel editor; the busy, off and fixed tools reused one widget key, so switching the selected person kept the previous person's selections and could save them onto the new person.
- **Decision**: `generate()` rejects non-text or whitespace-only names before reserving fixed duties; a failed fixed-duty validation resets the duty counters and schedule so no partial state survives; the busy, off and fixed multiselects key their widget state by person while their defaults still come from that person's saved values.
- **Consequences**: Invalid personnel fail fast with an actionable message; a failed fixed-duty validation leaves the editor at a zero counter baseline while the ADR-006 failed-search baseline behavior is unchanged; each person's tool selections are independent and are dropped on logout.

### ADR-008: Clear partial rosters on failure and emit RFC 5545 calendar lines
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: A failed search returned an empty roster but left the last partial attempt on `DutyScheduler.schedule`; the `.ics` export separated lines with bare LF and let long SUMMARY/DESCRIPTION lines exceed the 75-octet folding limit.
- **Decision**: Failed searches clear `schedule` together with restoring counters; `generate_ics` folds every content line at the RFC 5545 octet limit and joins the physical lines with CRLF.
- **Consequences**: Callers never observe a partial roster after a failed generation, and exports are accepted by strict iCalendar parsers; long name lists unfold identically in clients.

### ADR-009: Clear authentication form state on logout
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: `clear_user_state()` ran on logout but left the login and registration widget keys in session state, so the login page reappeared with the previous username and password already filled; the clear-database confirmation flag could also survive into the next session.
- **Decision**: Clear the login/registration fields and the username through a dedicated `clear_auth_state()` invoked only on the logout path, before the login page renders; treat `confirm_clear_db` as user-scoped state.
- **Consequences**: Logout leaves an empty login form and no previous identity; the login page recreates its widget keys with empty defaults, while a successful login never touches auth widgets that were already rendered in the same run.

### ADR-010: Scope previous-month history widgets to the selected month
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: The fixed `hist_p1`/`hist_p2` widget keys kept the selected names when the sidebar month changed, while the label pointed at a different previous-month date, so the roster could silently inherit the wrong rest-rule history.
- **Decision**: Include the selected year and month in the `hist_p1`/`hist_p2` widget keys.
- **Consequences**: Changing the month starts the history empty; Streamlit discards widget state that is not rendered on a run, so returning to an earlier month does not restore a stale selection, and the `hist_` prefix still clears everything on logout.

### ADR-011: Quarantine unreadable local state instead of failing the login
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: `load_db` and `load_users` parsed their JSON files directly, so a truncated `personnel_db_<user>.json` or `users_db.json` raised `JSONDecodeError` inside `main()` and the user could not open the app or log in; the damaged file also stayed in place, repeating the crash.
- **Decision**: Add `storage.load_json_or_default`, which returns a caller-supplied default and renames an unreadable file to `<name>.corrupt_<epoch>`; route both `load_db` and `load_users` through it.
- **Consequences**: A corrupt state file costs the saved roster or local accounts for that session but no longer blocks startup, and the quarantined bytes remain on disk for inspection. A missing file still returns the default without creating one.

### ADR-012: Derive a readable, month-scoped calendar title
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: The ICS export derived its title with `t["title"].split(" ")[0]`, which keeps only the leading wizard emoji in both languages, so every exported event was titled `🧙‍♂️ Duty: <names>` in calendar clients.
- **Decision**: Add `ui_helpers.calendar_title`, which drops a leading non-text token and any parenthetical, appends the roster month and year, and falls back to `Duty Roster`; the export call uses it.
- **Consequences**: Events read `Nöbet Wizard 2/2026` or `Nöbet Sihirbazı 2/2026`, and the helper is unit-tested for both languages and for emoji-only or empty titles.

### ADR-013: Use the width= API instead of the deprecated use_container_width
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: Streamlit logs a removal warning on every rerun for `use_container_width`, whose announced removal date (2025-12-31) has passed; the installed release supports the replacement `width=` argument on buttons, download buttons, dataframes and the data editor.
- **Decision**: Replace every `use_container_width=True` call site with `width="stretch"`.
- **Consequences**: Logs are clean and the UI keeps its existing full-width layout; the implicit minimum Streamlit version is one that accepts `width=`, which the unpinned `streamlit` requirement resolves to on install.

### ADR-014: Keep loaded, saved and cleared databases consistent with their rosters
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: `load_cloud_data` restored a saved roster only when the database contained one, so loading a roster-free database kept the previous session's roster active against the newly loaded personnel; `save_db` persisted the current roster even when saving an empty personnel list, so "Clear Personnel Database" wrote a document with a roster but no personnel.
- **Decision**: Loading clears `generated_schedule`, `schedule_success`, `gen_year` and `gen_month` before the optional restore, and `save_db` only persists a roster when the personnel list is non-empty.
- **Consequences**: A database always describes its personnel and roster consistently; loading a database never displays a roster left over from the previous session, and clearing the database leaves a roster-free document.

### ADR-015: Back off only failed logins
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: The login button slept one second before authentication on every attempt, so a correct login took about 1.5s while guessing scripts could still open parallel sessions unthrottled; the delay only punished legitimate users.
- **Decision**: Authenticate first; on success clear the session counter; on each failure increment `login_failures` and pause `security.login_backoff_seconds` (1s, 2s, then a 3s cap). The counter is auth-scoped and cleared on success and logout.
- **Consequences**: Valid logins return in about 0.1s, repeated failures in one session back off predictably, and the delay policy is pinned by unit tests instead of a sleep call.

### ADR-016: Treat malformed secrets and scalar admin entries as absent
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: `get_secrets()` returned Streamlit's lazy `st.secrets` object, so the TOML parse and the admin lookup happened inside `authenticate()`/`load_db()`. A malformed `.streamlit/secrets.toml` raised during login for every user, and a scalar `admin = "..."` entry raised `TypeError` (`string indices must be integers`); only a missing file was handled.
- **Decision**: Parse eagerly with `dict(st.secrets)` inside the existing guard so a missing or malformed file returns `{}`, and catch `(KeyError, TypeError)` around the admin lookup so a scalar or partial admin entry fails the check instead of crashing.
- **Consequences**: A broken secrets file degrades to local-account/admin-none login rather than a dead login page; a valid admin table still works, and misconfiguration is silent by design (logs are not available on Streamlit Cloud).

### ADR-017: Upgrade legacy SHA-256 password hashes to bcrypt on first login
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: Accounts registered before the bcrypt switch store an unsalted SHA-256 hex digest. `check_hashes` accepts only bcrypt hashes, so those users could not log in, locally or in Firestore, and saw only the generic failure message.
- **Decision**: `security.verify_password` accepts a 64-character hex digest with a constant-time compare and returns a fresh bcrypt hash. `authenticate` stores it after a successful login: `storage.replace_json_entry` re-reads the users file and replaces only that user while the old hash is still there, and Firestore gets an `update` of `password_hash`. A failed upgrade never blocks the login and retries on the next one.
- **Consequences**: Legacy accounts work again and leave the weak format on first login. The SHA-256 check stays until no active user has one; delete it then. The reload narrows the lost-update window on the users file but does not lock it, as registration already behaves.

### ADR-018: Keep every quarantined state file and keep it out of git
- **Date**: 2026-11-14
- **Status**: Accepted
- **Context**: ADR-011 renames an unreadable state file to `.corrupt_<epoch seconds>`. `os.replace` overwrites an existing target, so a second corruption within the same second destroyed the first quarantined copy. The runtime copies (`users_db.json.corrupt_*`, `personnel_db_*.json.corrupt_*`) were also not ignored by git, although they hold password hashes and personnel data.
- **Decision**: `load_json_or_default` appends `_1`, `_2`, ... while the quarantine name exists, and .gitignore covers `*_db.json.corrupt_*` and `personnel_db_*.json.corrupt_*`.
- **Consequences**: No damaged state is lost to a name collision and none can be staged by accident. Quarantined files still accumulate until the user removes them.

### ADR-019: Log in legacy accounts whose passwords exceed bcrypt's 72-byte limit without upgrading them
- **Date**: 2026-11-15
- **Status**: Accepted
- **Context**: ADR-017 rehashes a legacy SHA-256 account to bcrypt on its first login. Registration caps passwords at 72 bytes, but legacy accounts had no cap, and bcrypt 5 raises ValueError above 72 bytes (bcrypt 4 silently truncates), so such a user crashed the login page.
- **Decision**: verify_password returns (True, None) for a correct legacy password longer than 72 bytes: the login succeeds and the legacy hash stays. The limit is counted in UTF-8 bytes.
- **Consequences**: These accounts keep the weak hash until the password is changed to 72 bytes or fewer, and no bcrypt call can raise during login. ADR-017's removal condition for the SHA-256 check now also depends on these accounts.

### ADR-020: Normalize loaded state documents instead of trusting parsed JSON
- **Date**: 2026-11-15
- **Status**: Accepted
- **Context**: ADR-011 quarantines state files that fail to parse, but a document that parses can still be unusable: a number or null instead of an object, a null roster, a person without a gender, a setting of the wrong type. Each of these crashed the page on load, and the Firestore path returned the cloud document unchecked.
- **Decision**: A new state_documents module decides the shape. normalize_personnel_document returns None for an unusable whole (not an object or list, or personnel not a list), drops people without a name or an M or F gender, fills missing limits with the add-form defaults (5 duties, 2 weekends), and discards settings of the wrong type or range. load_json_or_default takes an accept check and quarantines a rejected document like a corrupt one. The users file must be an object. Local and Firestore documents use the same normalization, and load_db returns how many people were dropped so the page can warn.
- **Consequences**: Only an unusable whole is renamed; field-level problems are repaired in memory and the file is untouched until the next save, which would then remove the dropped entries, and the warning says so. Dropping a person without a valid gender loses that record on save, a deliberate trade against guessing a gender that drives the mixed-team rules.

### ADR-021: Refuse usernames that collide by case or with the admin, and anchor the username pattern
- **Date**: 2026-11-15
- **Status**: Accepted
- **Context**: Per-user files are named from the username, so on Windows and macOS the users Ann and ann shared one personnel file. A registered user named like the configured admin logged in through the local users file, which is checked before the admin secret, and received the admin's personnel file. re.match with a dollar sign also accepted a trailing newline.
- **Decision**: security.is_valid_username uses fullmatch. security.username_taken compares ignoring case against existing and reserved names, and registration reserves the admin username from secrets, locally and in Firestore. Login stays case-sensitive and no file is renamed, because renaming would orphan existing files on case-sensitive hosts.
- **Consequences**: New collisions are refused with the existing user-exists message. Collisions already present on a case-insensitive filesystem are not repaired. Firestore has no cheap exact case-insensitive lookup, so there only the admin name and exact duplicates are refused.

<!-- Entry format:
### ADR-NNN: <decision in one line>
- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Context**: <what forced the decision>
- **Decision**: <what was decided>
- **Consequences**: <what follows, including what it costs>
-->

## Licensing migration (agpl-final)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `agpl-final` remain under GNU AGPL-3.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.

## License notice cleanup (2026-10-26)

- The license-history notes were removed from README.md and COMMERCIAL.md: the project is offered only under the Aegean License 1.1 (AL-1.1), with commercial use under ACL-1.0.
