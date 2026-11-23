# CLAUDE.md

## What this is

A teacher's tool that collects student grades from CodeHS (AP CSP). It logs into codehs.com with Selenium, opens one assignment for each student in a hard-coded roster, reads the score, saves a screenshot, and shows the results in a Tkinter window. You can export the results to CSV or print them to the console.

## Running

```powershell
pipenv shell          # or: pipenv install, first time
python app_UI.py      # or: .\st.bat (PowerShell needs the .\ prefix)
```

- Needs `secret.py` in the repo root (gitignored), with `usr = "..."` and `psw = "..."` for the CodeHS login.
- Needs Chrome. Selenium 4.16 includes Selenium Manager, which fetches a matching chromedriver. If the driver is out of date, see https://googlechromelabs.github.io/chrome-for-testing/
- `Pipfile` pins Python 3.12. `__pycache__` also has 3.14 bytecode, so 3.14 has been used too.
- There are no tests, linter, or build step.

## Files

| File | Status | Purpose |
|---|---|---|
| `app_UI.py` | **Main app** | Tkinter UI + Selenium scraper. Everything that matters is here. |
| `st.bat` | Launcher | Runs `python app_UI.py` |
| `settings.db` | Runtime state | SQLite file. Stores the last section and assignment IDs (one row, `id=1`). |
| `screenshots/` | Output | One PNG per student per run: `scrn_<assignment>_<Last__First>_<YYYY_MM_DD--HH_MM_SS>.png`. Written-response pages go in a subfolder named after the assignment (from the tab title): `screenshots/<Assignment_Name>/<Last__First>_<timestamp>.png` |
| `app_UI copy.py` | Legacy | Older version that used `chromedriver_py` and `time.sleep` |
| `flask_app.py` | Legacy | Despite the name, not Flask. It's an early standalone Selenium script with an old roster and section 600389. |
| `db.py`, `database.db`, `templates/`, `static/` | Legacy / unused | Leftovers from an unfinished Flask app for student groups and grade uploads. No Flask routes exist, and `flask` isn't a dependency. |
| `.env` | Unused | `FLASK_APP` setting for that Flask app |
| `requirements.txt` | Mirror of the Pipfile | selenium==4.16.0, requests, beautifulsoup4 |

## How `app_UI.py` works

- **Settings persistence:** `initialize_database` / `get_default_settings` / `save_settings`. The settings are one upserted row in `settings.db`, at a path relative to the script. They're saved when the scraper starts and when the window closes. The row holds the section plus up to `NUM_ASSIGNMENTS` (4) assignment IDs in columns `assignment`, `assignment2`..`assignment4`. `initialize_database` adds missing columns to older DBs with `ALTER TABLE`.
- **Multiple assignments:** the UI has 4 assignment fields, and empty ones are skipped. `start_scraper_threaded` (main thread) reads the inputs, saves them, and rebuilds the Treeview columns with `configure_result_columns`, giving one score column per assignment headed by its ID. It then passes `(section, assignments)` to the worker. The worker's outer loop goes over students and its inner loop over assignments, and it inserts one row per student.
- **Roster:** the module-level `ROSTERS` dict (`"APCSP"`, `"AP Cyber"`), each a list of `("Last, First", "codehs_student_id")` pairs. The class buttons at the top of the window set `current_class`; `start_scraper_threaded` passes that roster to the worker. Each class's CodeHS section ID lives in the module-level `SECTIONS` dict; `on_class_change` fills the Section field from it (also at startup, so the section saved in `settings.db` is ignored on load). `get_code_*.py` parse `ROSTERS` from this file with `ast`. **Update this list each new school year or section.** The display name is used only for the results table and screenshot filenames. Navigation uses only the ID.
- **URL pattern:** `https://codehs.com/student/{student_id}/section/{section}/assignment/{assignment}`
- **Score extraction:** `extract_score_any_page` tries two page types in order:
  1. Programming assignment: clicks the "Check Code" button, then waits up to 60s until `#score-text` holds a numeric `N/M`. The page shows a placeholder until the autograder finishes.
  2. Quiz: reads `.stats-options-container .score-container`, then takes the text after `Score:`.
  3. Written response (e.g. AP Cyber tasks): no score on the page, so it returns the text of the `Status:` badge (e.g. `Submitted`). It ignores the "N points" badge, which shows points possible, not points earned.
  It returns `(score, is_written_response)`. It raises `TimeoutException` on the CodeHS "page not found" page or when none of the three are found. The default wait is 25s.
- **Threading:** the scraper runs on a daemon thread. UI updates must go through `root.after(0, ...)`. The per-student closures bind loop variables through default args (`n=display_name`). Keep that pattern.
- **Stop button:** `stop_scraper` sets `stop_event` and quits `active_driver` on a separate thread, which breaks any wait in progress. The worker checks `stop_event` between students and assignments, drops the partial row for the student it stopped on, and shows no error popup. Rows already scraped stay in the table.
- **Errors:** if one assignment fails, that cell shows `ERROR: ...` and the scraper moves on to the next assignment or student.
- **Output:** the CSV export and console print write one column per assignment and keep only the numerator (`"3/5"` becomes `"3"`), so the result can be pasted into a gradebook.
- `make_driver(headless=...)` accepts a flag, but headless mode is commented out, so the browser always opens visibly.

## Gotchas

- CodeHS DOM selectors (`login-email`, `login-password`, `logged-in-navbar`, `score-text`, the "Check Code" button text, quiz score classes) are brittle. When scraping breaks, check these first.
- The default section and assignment in `initialize_database` (`779844` / `193450569`) apply only when `settings.db` has no row yet.
- `settings.db` was created by an older schema (`AUTOINCREMENT`). The code's `CREATE TABLE IF NOT EXISTS` doesn't change it. The difference is harmless.
- **Privacy/secrets:** `screenshots/`, `static/uploads/` (Canvas grade exports with student emails), `__pycache__/` (including compiled `secret.*.pyc`), and `.env` are all committed. Don't push this repo publicly without removing those files and adding them to `.gitignore`.
