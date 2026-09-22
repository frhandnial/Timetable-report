"""Interactive CMISGo login helper intended for Codex-run sessions.

It opens a visible browser for Sheffield CAS/MFA, writes progress to
``login_status.txt`` so Codex can inspect it after starting the process in the
background, and saves the reusable Playwright session to
``storage_state.json`` once the authenticated timetable page is reached.

Usage:
    python scripts/codex_login_setup.py
    python scripts/codex_login_setup.py --timeout 900
"""

import argparse
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
PROFILE_DIR = HERE / "browser_profile"
STATE_FILE = HERE / "storage_state.json"
DUMP_FILE = HERE / "timetable_dump.html"
STATUS_FILE = HERE / "login_status.txt"
TIMETABLE_URL = "https://cmisgostudents.shef.ac.uk/CMISGo/Web/Timetable"


def status(message: str) -> None:
    """Record a user-visible status for both terminal and Codex checks."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    STATUS_FILE.write_text(line + "\n", encoding="utf-8")
    print(line, flush=True)


def is_authenticated_cmisgo(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.hostname == "cmisgostudents.shef.ac.uk"
        and "/cas/login" not in parsed.path.lower()
    )


def main(timeout: int) -> int:
    PROFILE_DIR.mkdir(exist_ok=True)
    status("Opening Chromium. Complete Sheffield CAS and MFA in the browser.")

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TIMETABLE_URL, wait_until="domcontentloaded")

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for candidate in context.pages:
                if is_authenticated_cmisgo(candidate.url):
                    try:
                        candidate.wait_for_load_state("domcontentloaded", timeout=15_000)
                    except Exception:
                        pass
                    context.storage_state(path=str(STATE_FILE))
                    DUMP_FILE.write_text(candidate.content(), encoding="utf-8")
                    status(f"Saved authenticated session to {STATE_FILE}")
                    context.close()
                    return 0

            remaining = max(0, int(deadline - time.monotonic()))
            urls = [candidate.url for candidate in context.pages]
            status(f"Awaiting authenticated CMISGo page; {remaining}s remaining. URLs: {urls}")
            time.sleep(5)

        context.close()

    status("Timed out: no session saved. Keep the browser open on the timetable page.")
    return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save CMISGo login for Codex")
    parser.add_argument("--timeout", type=int, default=900, help="login wait time in seconds")
    args = parser.parse_args()
    raise SystemExit(main(args.timeout))
