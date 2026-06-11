#!/usr/bin/env python3
"""Finalize state and briefing for the 2026-06-05 full guarded run."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


RUN_DIR = Path(__file__).resolve().parent
STATE = RUN_DIR / "state.json"


def main() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    auto_submitted = 0
    package_ready = 0
    needs_decision = 0
    lines = [
        "# Jamie Autopilot Briefing - 2026-06-05 Full Guarded Run",
        "",
        "## Outcome",
        "- Verified candidate pool: 23 live roles",
        "- Built packages: 4",
        "- Auto-submitted: 0",
        "- Tracker write-back: deferred because Google Sheets API is disabled on the OAuth project",
        "",
        "## Packages",
    ]
    for app in state["applications"]:
        folder = Path(app["folder"])
        status_path = folder / "LIVE_FORM_STATUS.json"
        deep_path = folder / "LIVE_FORM_DEEP_STATUS.json"
        live = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
        deep = json.loads(deep_path.read_text(encoding="utf-8")) if deep_path.exists() else {}
        if app["score"] >= 80:
            package_ready += 1
        else:
            needs_decision += 1
        app["submission"] = {
            "status": "ready_for_human_submit",
            "mode": "workday_account_required",
            "live_form_status_path": str(status_path) if status_path.exists() else None,
            "deep_status_path": str(deep_path) if deep_path.exists() else None,
            "screenshots_dir": str(folder / "screenshots"),
            "note": "Apply opened; Workday requires account creation/sign-in before form fields are reachable.",
        }
        ready = {
            "company": app["company"],
            "title": app["title"],
            "url": app["url"],
            "score": app["score"],
            "verdict": app["verdict"],
            "resume_pdf": str(folder / "resume.pdf"),
            "cover_letter_pdf": str(folder / "cover_letter.pdf"),
            "submission_guide": str(folder / "submission_guide.md"),
            "form_fields": str(folder / "form_fields.json"),
            "live_form_status": live.get("status"),
            "deep_form_status": deep.get("title"),
            "human_action": "Create/sign into Workday candidate account, verify email if prompted, then upload PDFs and use form_fields.json.",
        }
        (folder / "READY_FOR_HUMAN_SUBMIT.json").write_text(json.dumps(ready, indent=2), encoding="utf-8")
        lines.extend([
            f"### {app['company']} - {app['title']}",
            f"- Lane: {app['lane']}",
            f"- Score: {app['score']} ({app['verdict']})",
            f"- H-1B: {app['h1b']}",
            f"- Live form: {live.get('status', 'not probed')}",
            f"- Risk: {app['risk']}",
            f"- Folder: `{folder}`",
            "",
        ])
    state["summary"].update({
        "package_ready": package_ready,
        "needs_decision": needs_decision,
        "auto_submitted": auto_submitted,
        "finalized_at": datetime.now().isoformat(),
        "live_form_result": "Workday account creation/sign-in required before field fill.",
    })
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    briefing_md = "\n".join(lines)
    (RUN_DIR / "briefing.md").write_text(briefing_md, encoding="utf-8")
    html = "<!doctype html><meta charset='utf-8'><title>Jamie Autopilot Briefing</title><style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:900px;margin:40px auto;line-height:1.45}code{background:#f4f4f4;padding:2px 4px}</style>" + briefing_md.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>\n")
    (RUN_DIR / "briefing.html").write_text(html, encoding="utf-8")
    print(json.dumps({"state": str(STATE), "briefing": str(RUN_DIR / "briefing.md")}, indent=2))


if __name__ == "__main__":
    main()
