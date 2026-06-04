#!/usr/bin/env python3
"""Flip Jamie's tracker (2026 tab) row 49 column A (Mercury status) Applied -> Rejection.
Connects to the logged-in debug Chrome on CDP 9333. Screenshots before + after for audit.
Surgical: edits ONE cell only. Verifies the target row is Mercury before writing."""
import sys, time
from patchright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9333"
GID = "1018026840"
SHEET = f"https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/edit#gid={GID}"
OUTDIR = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-02_night"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    # reuse existing sheet tab if open, else new
    page = None
    for pg in ctx.pages:
        if "1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E" in pg.url:
            page = pg
            break
    if page is None:
        page = ctx.new_page()
        page.goto(SHEET, wait_until="load")
    page.bring_to_front()
    time.sleep(3)

    # SAFETY RE-VERIFY via gviz that row 49 is Mercury before editing anything
    import csv, io
    body = ctx.request.get(
        f"https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/gviz/tq?tqx=out:csv&gid={GID}"
    ).text()
    rows = list(csv.reader(io.StringIO(body)))
    r49 = rows[48] if len(rows) >= 49 else []
    comp = r49[3].strip() if len(r49) > 3 else ""
    stat = r49[0].strip() if len(r49) > 0 else ""
    print(f"PRECHECK row49: status='{stat}' company='{comp}'")
    if comp != "Mercury":
        print("ABORT: row 49 is not Mercury — refusing to edit.")
        sys.exit(2)
    if stat == "Rejection":
        print("NOOP: row 49 already 'Rejection'. Nothing to do.")
        sys.exit(0)

    page.screenshot(path=OUTDIR + r"\sheet_before.png")

    # Focus the grid canvas first (click center of the visible sheet), then drive via keyboard.
    box = page.viewport_size
    page.mouse.click(box["width"] // 2, box["height"] // 2)
    time.sleep(0.6)
    page.keyboard.press("Escape")
    time.sleep(0.3)

    # Open the Name Box with its keyboard accelerator, then jump to A49.
    # The reliable Sheets name box input has class 'waffle-name-box'.
    nb = page.query_selector(".waffle-name-box") or page.query_selector("#t-name-box input") or page.query_selector("#t-name-box")
    if nb is None:
        print("ABORT: could not locate the Name Box element.")
        sys.exit(3)
    nb.click()
    time.sleep(0.4)
    page.keyboard.press("Control+A")
    page.keyboard.type("A49")
    page.keyboard.press("Enter")
    time.sleep(1.0)
    page.screenshot(path=OUTDIR + r"\sheet_nav.png")
    # Overwrite the selected cell
    page.keyboard.type("Rejection")
    time.sleep(0.3)
    page.keyboard.press("Enter")
    time.sleep(1.8)
    page.screenshot(path=OUTDIR + r"\sheet_after.png")

    # VERIFY via gviz re-read
    body2 = ctx.request.get(
        f"https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/gviz/tq?tqx=out:csv&gid={GID}"
    ).text()
    rows2 = list(csv.reader(io.StringIO(body2)))
    r49b = rows2[48] if len(rows2) >= 49 else []
    newstat = r49b[0].strip() if len(r49b) > 0 else ""
    newcomp = r49b[3].strip() if len(r49b) > 3 else ""
    print(f"POSTCHECK row49: status='{newstat}' company='{newcomp}'")
    print("RESULT:", "OK" if (newstat == "Rejection" and newcomp == "Mercury") else "FAILED")
