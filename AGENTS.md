# AGENTS.md

This repository's agent instructions live in [CLAUDE.md](CLAUDE.md). Read it before changing code; the
dated sections near the end (latest: "2026-09 Audit Remediation") override older text.

Quick reference:

- Tests: `python -m unittest discover -s tests -q` (network-free; set `QT_QPA_PLATFORM=offscreen` for GUI tests).
- Type check: `pyright .`
- Do not modify scraper parsing selectors (`scrapers/`) or `scrapers/stealth.py`.
- Do not change existing DB table structures; add new tables instead.
- Settings mixins must resolve their window via `gui/settings_panels/host.py`, not `self.parent()`.
- Never call `asyncio.set_event_loop_policy` (Playwright needs the Windows Proactor loop).
- Feature work follows Spec Kit: `specs/<id>/spec.md` → `plan.md` → `tasks.md`.
- Latest audit and remediation status: [PROJECT_AUDIT.md](PROJECT_AUDIT.md), `specs/001-audit-remediation/`.
