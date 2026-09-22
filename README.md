# CMISGo Timetable Report

Pulls your University of Sheffield CMISGo timetable (the one behind
`https://cmisgostudents.shef.ac.uk/CMISGo/Web/Timetable`, protected by
Sheffield's CAS single sign-on + MFA) and turns it into a clean weekly
or monthly report, without screenshotting anything.

It works by reusing the same internal JSON API the CMISGo web app
itself calls to draw your calendar (`Appointments/Month/...`), rather
than scraping the rendered page.

## How it works

MFA can't be fully automated, so this is a two-step setup:

1. **`login_setup.py`** — opens a real (visible) browser window pointed
   at the timetable. You log in by hand (username, password, MFA), same
   as normal. Once it detects you've reached the actual timetable page,
   it captures your session cookies to `storage_state.json` and closes.
2. **`get_timetable.py`** — reuses that saved session to fetch your
   timetable data headlessly (no visible window) and prints/exports a
   report. No further login needed until the session expires.

When the saved session eventually expires, just rerun `login_setup.py`.

## Setup

```
pip install -r requirements.txt
python -m playwright install chromium
```

## Usage

Log in once (or whenever your session has expired):

```
python scripts/login_setup.py
```

When launching the login flow through Codex, use the companion helper instead.
It writes a local status file while it waits for the authenticated CMISGo page:

```
python scripts/codex_login_setup.py
```

Then fetch a report:

```
python scripts/get_timetable.py                       # current week, printed to console
python scripts/get_timetable.py --offset 1             # next week
python scripts/get_timetable.py --offset -1            # last week
python scripts/get_timetable.py --csv                  # also write a CSV to ./reports/
python scripts/get_timetable.py --xlsx                 # write a formatted Excel timetable with Week 1, Week 2, ... headings
python scripts/get_timetable.py --month 2026-10 --csv  # a full calendar month
python scripts/get_timetable.py --from 2026-09-28 --to 2026-12-25 --xlsx  # an inclusive date range as formatted Excel
python scripts/get_timetable.py --month 2026-10 --out "C:\path\to\file.csv"  # exact output path
```

### Flags

| Flag | Meaning |
|---|---|
| `--offset N` | Weeks from the current week (0 = this week, 1 = next week, -1 = last week). Ignored if `--month` is set. |
| `--month YYYY-MM` | Fetch a full calendar month instead of a week. |
| `--from YYYY-MM-DD` / `--to YYYY-MM-DD` | Fetch an inclusive custom date range. Use the two flags together. |
| `--csv` | Also write a CSV into `./reports/timetable_<date>.csv`. |
| `--out PATH` | Write the CSV to an exact path instead (implies `--csv`). |
| `--xlsx` | Write a formatted Excel workbook with merged weekly headings, wrapped cells, and printable layout. |
| `--out-xlsx PATH` | Write the Excel workbook to an exact path instead (implies `--xlsx`). |

## Notes

- `storage_state.json` and `browser_profile/` hold your live login
  session — never commit them (already gitignored).
- CMISGo's own `Appointments/Month/<id>/...` endpoint doesn't map `id`
  linearly to calendar dates, so for wider queries (`--month`, or an
  `--offset` more than 1 week away) the script scans a small
  neighbourhood of ids around whatever id the site itself used on page
  load and merges the results. This is fast (a couple seconds) and
  self-corrects if Sheffield changes their internal numbering.
