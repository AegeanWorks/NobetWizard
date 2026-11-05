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
