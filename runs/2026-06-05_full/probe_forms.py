#!/usr/bin/env python3
"""Probe live ATS forms for today's packages via the debug Chrome CDP port."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


RUN_DIR = Path(__file__).resolve().parent
DEBUG_URL = "http://127.0.0.1:9333"


def textish(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""


def screenshot(page, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(path), full_page=True)
    except Exception:
        page.screenshot(path=str(path), full_page=False)


def click_apply(page) -> str:
    patterns = [
        re.compile(r"^Apply$", re.I),
        re.compile(r"Apply Now", re.I),
        re.compile(r"Start Your Application", re.I),
    ]
    for pattern in patterns:
        try:
            btn = page.get_by_role("button", name=pattern).first
            if btn.count() and btn.is_visible(timeout=2500):
                btn.click()
                return f"clicked button {pattern.pattern}"
        except Exception:
            pass
        try:
            link = page.get_by_role("link", name=pattern).first
            if link.count() and link.is_visible(timeout=2500):
                link.click()
                return f"clicked link {pattern.pattern}"
        except Exception:
            pass
    try:
        page.locator("text=/Apply/i").first.click(timeout=5000)
        return "clicked text=/Apply/i"
    except Exception as exc:
        return f"apply control not found: {exc}"


def fill_reachable_basics(page, role_dir: Path) -> dict:
    fields = json.loads((role_dir / "form_fields.json").read_text(encoding="utf-8"))
    filled = []
    values = {
        "first": fields["first_name"],
        "last": fields["last_name"],
        "email": fields["email"],
        "phone": fields["phone"],
        "address": fields["address_line_1"],
        "city": fields["city"],
        "zip": fields["zip"],
        "linkedin": fields["linkedin_url"],
    }
    selectors = [
        ("first", "input[name*='first' i], input[id*='first' i]"),
        ("last", "input[name*='last' i], input[id*='last' i]"),
        ("email", "input[type='email'], input[name*='email' i], input[id*='email' i]"),
        ("phone", "input[type='tel'], input[name*='phone' i], input[id*='phone' i]"),
        ("address", "input[name*='address' i], input[id*='address' i]"),
        ("city", "input[name*='city' i], input[id*='city' i]"),
        ("zip", "input[name*='postal' i], input[name*='zip' i], input[id*='postal' i], input[id*='zip' i]"),
        ("linkedin", "input[name*='linkedin' i], input[id*='linkedin' i]"),
    ]
    for key, sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=1000):
                loc.fill(values[key])
                filled.append(key)
        except Exception:
            pass
    upload_results = []
    try:
        inputs = page.locator("input[type='file']")
        count = min(inputs.count(), 2)
        if count >= 1:
            inputs.nth(0).set_input_files(str(role_dir / "resume.pdf"))
            upload_results.append("resume")
            time.sleep(1)
        if count >= 2 and (role_dir / "cover_letter.pdf").exists():
            inputs.nth(1).set_input_files(str(role_dir / "cover_letter.pdf"))
            upload_results.append("cover_letter")
            time.sleep(1)
    except Exception as exc:
        upload_results.append(f"upload_error: {exc}")
    return {"filled": filled, "uploads": upload_results}


def probe(role_dir: Path, context) -> dict:
    role = json.loads((role_dir / "evaluation.json").read_text(encoding="utf-8"))
    shots = role_dir / "screenshots"
    shots.mkdir(exist_ok=True)
    page = context.new_page()
    page.set_default_timeout(12000)
    result = {
        "role_dir": str(role_dir),
        "company": role["company"],
        "title": role["title"],
        "url": role["url"],
        "started_at": datetime.now().isoformat(),
        "actions": [],
        "status": "unknown",
    }
    try:
        page.goto(role["url"], wait_until="domcontentloaded", timeout=45000)
        page.wait_for_load_state("networkidle", timeout=15000)
    except PlaywrightTimeoutError:
        result["actions"].append("navigation timed out after DOM loaded")
    page.wait_for_timeout(3000)
    screenshot(page, shots / "01_landing.png")
    result["landing_title"] = page.title()
    result["actions"].append(click_apply(page))
    page.wait_for_timeout(6000)
    screenshot(page, shots / "02_after_apply_click.png")
    body = textish(page)
    low = body.lower()
    result["after_apply_url"] = page.url
    result["after_apply_title"] = page.title()
    result["body_preview"] = body[:2500]
    if any(x in low for x in ["sign in", "create account", "candidate home", "myworkdayjobs.com/en-us/"]):
        result["status"] = "login_or_account_required"
    if any(x in low for x in ["captcha", "verify you are human", "recaptcha", "hcaptcha"]):
        result["status"] = "captcha_or_human_check"
    fill = fill_reachable_basics(page, role_dir)
    if fill["filled"] or fill["uploads"]:
        result["actions"].append(f"filled={fill['filled']} uploads={fill['uploads']}")
        page.wait_for_timeout(2000)
        screenshot(page, shots / "03_after_reachable_fill.png")
        if result["status"] == "unknown":
            result["status"] = "partially_filled_ready_for_review"
    if result["status"] == "unknown":
        result["status"] = "opened_apply_unfilled"
    result["finished_at"] = datetime.now().isoformat()
    (role_dir / "LIVE_FORM_STATUS.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    role_dirs = [Path(arg).resolve() for arg in sys.argv[1:]]
    if not role_dirs:
        state = json.loads((RUN_DIR / "state.json").read_text(encoding="utf-8"))
        role_dirs = [Path(app["folder"]) for app in state["applications"][:2]]
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(DEBUG_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        results = [probe(role_dir, context) for role_dir in role_dirs]
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
