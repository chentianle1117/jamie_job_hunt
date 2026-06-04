#!/usr/bin/env python3
"""Read the 2026 tab of Jamie's tracker via Patchright CDP (port 9333) to find exact row positions.
Read-only: dumps column A (status) + column D (company) for rows 1..80 so we target the right cells."""
import os
from patchright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9333"
SHEET_GViz = ("https://docs.google.com/spreadsheets/d/1tRN3KMGHOSyRMf14TRUj3wPldbM9fwDxVu9XsEH6s2E/"
              "gviz/tq?tqx=out:csv&gid=1018026840")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]
    # Use the authenticated context's request API (session cookies) to fetch CSV directly
    resp = ctx.request.get(SHEET_GViz)
    body = resp.text()

import csv, io, json
rows = list(csv.reader(io.StringIO(body)))
out = {"total_rows": len(rows), "rows": [], "mercury_row": None, "last_data_row": 0}
for i, r in enumerate(rows, start=1):
    status = r[0].strip() if len(r) > 0 else ""
    company = r[3].strip() if len(r) > 3 else ""
    nonempty = any(c.strip() for c in r)
    if nonempty:
        out["last_data_row"] = i
    if company == "Mercury":
        out["mercury_row"] = i
    if nonempty:
        out["rows"].append({"row": i, "status": status, "company": company})
out["append_at"] = out["last_data_row"] + 1
with open(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-06-02_night\sheet_rows.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("wrote sheet_rows.json | total", out["total_rows"], "| mercury", out["mercury_row"], "| append_at", out["append_at"])
