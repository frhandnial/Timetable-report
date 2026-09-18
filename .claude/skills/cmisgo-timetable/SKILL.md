---
name: cmisgo-timetable
description: Fetch a University of Sheffield CMISGo timetable (weekly or a full calendar month) as a console report and/or CSV. Use when the user asks for their timetable, class schedule, lecture schedule, or a weekly/monthly report from CMISGo/Sheffield.
---

This skill wraps two Python scripts at the repo root (`scripts/login_setup.py`
and `scripts/get_timetable.py`) that pull a Sheffield CMISGo timetable via
the site's own internal JSON API (`Appointments/Month/...`), reusing a saved
browser session instead of scraping the rendered page or taking screenshots.

Requirements: Python 3 with `playwright` installed
(`pip install -r requirements.txt` then `python -m playwright install chromium`
from the repo root, once).

## Step 1 — check for a usable session

Check whether `storage_state.json` exists at the repo root. If it doesn't,
skip straight to Step 2.

## Step 2 — log in if needed

MFA cannot be automated. If there's no `storage_state.json`, or
`get_timetable.py` reports the session expired ("Session expired or not
logged in..."), run:

```
python scripts/login_setup.py
```

This opens a **visible** browser window. Tell the user a window has opened
and ask them to log in with their Sheffield username, password, and MFA in
that window — do not attempt to fill in credentials yourself. Wait for the
script to print "Login detected. Session cookies saved to ..." (it polls for
up to 10 minutes). If it times out, say so and offer to rerun it.

## Step 3 — fetch the report

Once a session exists, run `scripts/get_timetable.py` headlessly (no popup
needed) with flags matching what the user asked for:

- Current week (default): `python scripts/get_timetable.py`
- A specific week: `python scripts/get_timetable.py --offset N` (N weeks
  from the current week; negative for past weeks)
- A full calendar month: `python scripts/get_timetable.py --month YYYY-MM`
- Add `--csv` to also save a CSV under `./reports/`, or `--out <path>` to
  save it to an exact location the user asked for (e.g. their Downloads
  folder) — this implies `--csv`.

Print the console report back to the user, and if a CSV was written,
mention exactly where.

## Notes for whoever (or whatever) is running this

- Never commit or print the contents of `storage_state.json` or
  `browser_profile/` — they contain live session cookies.
- If the user asks for a wide date range, `get_timetable.py` already
  handles it internally (it scans a small neighbourhood of internal
  period ids and merges results) — just pass `--month` or a bigger
  `--offset`, no extra work needed.
- If the user wants this saved somewhere specific (e.g. "put it in
  Downloads"), use `--out` with that exact path and a stable filename —
  overwrite in place on repeat runs rather than creating dated duplicates,
  unless the user asks for a history of separate files.
