"""
One-time (or occasional) interactive login step.

Opens a real, visible Chromium window pointed at the CMISGo timetable.
You log in manually (username, password, MFA) in that window, same as
you would in any browser. Once the script detects you've reached the
actual timetable page, it saves the browser session (cookies/storage)
to disk in ./browser_profile so future runs of get_timetable.py can
reuse it without you logging in again.

It also dumps the timetable page's HTML to timetable_dump.html so the
page structure can be inspected once, to build the real data-scraping
script.

Run: python login_setup.py
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
PROFILE_DIR = HERE / "browser_profile"
STATE_FILE = HERE / "storage_state.json"
DUMP_FILE = HERE / "timetable_dump.html"
TIMETABLE_URL = "https://cmisgostudents.shef.ac.uk/CMISGo/Web/Timetable"

TIMEOUT_SECONDS = 600  # 10 minutes to complete login + MFA


def main():
    PROFILE_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TIMETABLE_URL)

        print("A browser window has opened.")
        print("Please log in with your Sheffield username, password, and MFA.")
        print(f"Waiting up to {TIMEOUT_SECONDS // 60} minutes for you to reach the timetable page...")

        start = time.time()
        reached_page = None
        tick = 0
        while time.time() - start < TIMEOUT_SECONDS:
            tick += 1
            pages = context.pages
            if tick % 3 == 0:
                print(f"  [poll {tick}] {len(pages)} tab(s): {[pg.url for pg in pages]}")
            for pg in pages:
                url = pg.url
                if "cmisgostudents.shef.ac.uk" in url and "cas/login" not in url and "login.shef.ac.uk" not in url:
                    reached_page = pg
                    break
            if reached_page:
                break
            time.sleep(1)

        if not reached_page:
            print("Timed out waiting for login. Nothing was saved. Run this script again.")
            context.close()
            return

        try:
            reached_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        DUMP_FILE.write_text(reached_page.content(), encoding="utf-8")
        context.storage_state(path=str(STATE_FILE))
        print(f"Login detected. Session cookies saved to {STATE_FILE}")
        print(f"Page HTML dumped to {DUMP_FILE} for inspection.")
        context.close()


if __name__ == "__main__":
    main()
