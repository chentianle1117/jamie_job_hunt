#!/usr/bin/env python3
"""
render_pdfs.py — Production PDF renderer for Jamie's job applications.
Uses Playwright (Chromium) to render resume.json → resume.pdf
and cover_letter.md → cover_letter.pdf.
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ORACLE_DIR = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search")
APPS_DIR = ORACLE_DIR / "outputs" / "2026-05-25-night" / "applications"
SCREENSHOTS_DIR = ORACLE_DIR / "outputs" / "2026-05-25-night" / "screenshots"
VIEWER_HTML = ORACLE_DIR / "resume_viewer.html"

ROLES = [
    "carlosrosario_ld_2026-05-25",
    "uportland_progmgrcommunity_2026-05-25",
    "pacificseafood_tds_2026-05-25",
    "aurora_pmpplteam_2026-05-25",
    "sandvik_hr_2026-05-25",
    "uportland_progmgrsocialjustice_2026-05-25",
]

# ── Read viewer HTML once ──────────────────────────────────────────────────────
VIEWER_HTML_CONTENT = VIEWER_HTML.read_text(encoding="utf-8")


def expand_kw(text):
    """Strip {kwg|text} markers → just text (clean mode for PDF)."""
    if not text:
        return ""
    return re.sub(r'\{(\w+)\|([^}]+)\}', r'\2', text)


def build_resume_html(data):
    """Build standalone print-ready resume HTML from resume.json data."""
    d = data
    meta = d.get("meta", {})
    margins = meta.get("pageMargins", {})
    top = margins.get("top", "0.35in")
    right = margins.get("right", "0.45in")
    bottom = margins.get("bottom", "0.35in")
    left = margins.get("left", "0.45in")

    header = d.get("header", {})
    summary = expand_kw(d.get("summary", ""))
    experience = d.get("experience", [])
    education = d.get("education", [])
    projects = d.get("projects", [])
    skills = d.get("skills", [])

    # Build experience HTML
    exp_html = ""
    for job in experience:
        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        dates = job.get("dates", "")
        ws_url = job.get("workSampleUrl")
        bullets = job.get("bullets", [])

        title_extra = ""
        if ws_url:
            title_extra = f' <a class="work-sample" href="{ws_url}" target="_blank">(Work Sample)</a>'

        bullets_html = ""
        for b in bullets:
            text = expand_kw(b.get("text", "") if isinstance(b, dict) else b)
            bullets_html += f"<li>&bull; {text}</li>\n"

        exp_html += f"""
<div class="job">
  <div class="job-title-row">
    <div class="job-title">{title}{title_extra}</div>
    <div class="job-location">{location}</div>
  </div>
  <div class="job-company-row">
    <div class="job-company">{company}</div>
    <div class="job-dates">{dates}</div>
  </div>
  <ul>{bullets_html}</ul>
</div>"""

    # Build education HTML
    edu_html = ""
    for edu in education:
        school = edu.get("school", "")
        loc = edu.get("location", "")
        degree = edu.get("degree", "")
        dates = edu.get("dates", "")
        edu_bullets = edu.get("bullets", [])
        edu_bullets_html = ""
        for b in edu_bullets:
            edu_bullets_html += f"<li>&bull; {b}</li>\n"
        bullet_block = f"<ul>{edu_bullets_html}</ul>" if edu_bullets_html else ""

        edu_html += f"""
<div class="edu">
  <div class="edu-row">
    <div class="edu-school">{school}</div>
    <div class="edu-location">{loc}</div>
  </div>
  <div class="edu-row">
    <div class="edu-degree">{degree}</div>
    <div class="edu-dates">{dates}</div>
  </div>
  {bullet_block}
</div>"""

    # Build projects HTML
    proj_html = ""
    for p in projects:
        proj_html += f"<li>{p}</li>\n"

    # Build skills HTML
    skills_html = ""
    for s in skills:
        skills_html += f"<li>{expand_kw(s)}</li>\n"

    loc = header.get("location", "Portland, OR (Open to Remote or Relocation)")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  :root {{
    --body-font-size: 9.5pt;
    --bullet-font-size: 9.2pt;
    --summary-font-size: 9pt;
    --header-name-size: 19pt;
    --header-contact-size: 8.8pt;
    --section-header-size: 9pt;
    --job-title-size: 9.5pt;
    --work-sample-size: 7.5pt;
    --body-line-height: 1.18;
    --bullet-line-height: 1.28;
    --summary-line-height: 1.30;
    --summary-margin: 4pt 0;
    --section-header-margin: 6pt 0 3pt 0;
    --job-margin-bottom: 7pt;
    --edu-margin-bottom: 5pt;
    --edu-ul-margin-top: 2pt;
    --page-margin-top: {top};
    --page-margin-right: {right};
    --page-margin-bottom: {bottom};
    --page-margin-left: {left};
    --accent-color: #2a6496;
  }}
  @page {{
    size: letter;
    margin: 0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Calibri','Helvetica Neue','Arial',sans-serif;
    font-size: var(--body-font-size);
    line-height: var(--body-line-height);
    color: #1a1a1a;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    padding: var(--page-margin-top) var(--page-margin-right) var(--page-margin-bottom) var(--page-margin-left);
  }}
  .header {{ text-align: center; margin-bottom: 2pt; }}
  .header h1 {{ font-size: var(--header-name-size); font-weight: bold; letter-spacing: 0.3pt; margin-bottom: 5pt; color: #000; }}
  .header .contact {{ font-size: var(--header-contact-size); color: #333; }}
  .header .contact a {{ color: var(--accent-color); text-decoration: underline; }}
  .summary {{
    padding: 4pt 7pt; margin: var(--summary-margin);
    font-size: var(--summary-font-size); line-height: var(--summary-line-height);
    font-style: italic; color: #222; text-align: center;
  }}
  .summary b {{ font-style: italic; font-weight: bold; }}
  .section-header {{
    text-align: center; font-size: var(--section-header-size); font-weight: bold;
    letter-spacing: 0.8pt; text-transform: uppercase;
    border-bottom: 1px solid #000; padding: 1pt 0;
    margin: var(--section-header-margin);
  }}
  .job {{ margin-bottom: var(--job-margin-bottom); }}
  .job-title-row {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .job-title {{ font-weight: bold; font-size: var(--job-title-size); }}
  .job-title .work-sample, .job-title a.work-sample {{
    font-weight: normal; font-size: var(--work-sample-size);
    text-decoration: underline; color: var(--accent-color);
  }}
  .job-location {{ font-size: var(--job-title-size); text-align: right; white-space: nowrap; }}
  .job-company-row {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .job-company {{ color: var(--accent-color); font-size: var(--job-title-size); }}
  .job-dates {{ font-style: italic; font-size: var(--job-title-size); text-align: right; white-space: nowrap; color: var(--accent-color); }}
  .job ul {{ margin: 2pt 0 0 8pt; padding: 0; list-style: none; }}
  .job li {{ font-size: var(--bullet-font-size); line-height: var(--bullet-line-height); margin-bottom: 0.5pt; padding-left: 1pt; }}
  .edu {{ margin-bottom: var(--edu-margin-bottom); }}
  .edu-row {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .edu-school {{ font-weight: bold; font-size: var(--job-title-size); }}
  .edu-location {{ font-size: var(--job-title-size); text-align: right; }}
  .edu-degree {{ font-size: var(--job-title-size); }}
  .edu-dates {{ font-style: italic; font-size: var(--job-title-size); text-align: right; color: var(--accent-color); }}
  .edu ul {{ margin: var(--edu-ul-margin-top) 0 0 12pt; padding: 0; list-style: none; }}
  .edu li {{ font-size: var(--bullet-font-size); line-height: 1.35; }}
  .simple-list {{ margin: 0; padding: 0; list-style: none; }}
  .simple-list li {{ font-size: var(--bullet-font-size); line-height: 1.38; margin-bottom: 1.5pt; }}
  .simple-list li b {{ font-weight: bold; }}
</style>
</head>
<body>
<div class="header">
  <h1>Jamie (Yi-Chieh) Cheng</h1>
  <div class="contact">
    {loc} &bull; (213) 700-3831 &bull;
    <a href="mailto:jamiecheng0103@gmail.com">jamiecheng0103@gmail.com</a> &bull;
    <a href="http://www.linkedin.com/in/jamieyccheng">LinkedIn</a>
  </div>
</div>

<div class="summary">{summary}</div>

<div class="section-header">Professional Experience</div>
{exp_html}

<div class="section-header">Education</div>
{edu_html}

<div class="section-header">Projects &amp; Awards</div>
<ul class="simple-list">
{proj_html}
</ul>

<div class="section-header">Skills</div>
<ul class="simple-list">
{skills_html}
</ul>

</body>
</html>"""
    return html


def build_cover_html(md_content):
    """Convert cover letter markdown to clean, print-ready HTML."""
    lines = md_content.strip().split("\n")
    body_lines = []
    in_header = True
    after_rule = 0

    for line in lines:
        stripped = line.strip()

        # Skip markdown headers (# ##)
        if stripped.startswith("#"):
            continue
        # Skip bold lines like **Jamie...**
        if stripped.startswith("**") and stripped.endswith("**"):
            continue
        # Count horizontal rules
        if stripped == "---":
            after_rule += 1
            if after_rule == 1:
                # After first rule = date block starts
                body_lines.append('<hr style="border:none;border-top:1px solid #ccc;margin:8pt 0;">')
            elif after_rule == 2:
                # After second rule = letter body starts
                body_lines.append('<hr style="border:none;border-top:1px solid #ccc;margin:8pt 0;">')
            continue

        if not stripped:
            body_lines.append('<br>')
            continue

        # Convert **bold** markers
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
        body_lines.append(f"<p>{formatted}</p>")

    body_html = "\n".join(body_lines)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: letter;
    margin: 0;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Calibri','Helvetica Neue','Arial',sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #1a1a1a;
    padding: 0.7in 0.75in 0.7in 0.75in;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  p {{ margin-bottom: 6pt; }}
  strong {{ font-weight: bold; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin: 8pt 0; }}
</style>
</head>
<body>
{body_html}
</body>
</html>"""


def count_pdf_pages(pdf_path):
    """Count pages in a PDF using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as e:
        return -1  # unknown


def render_role(role_id, page, is_carlos=False, screenshots_dir=None):
    """Render resume.pdf and cover_letter.pdf for a single role. Returns report dict."""
    role_dir = APPS_DIR / role_id
    resume_json_path = role_dir / "resume.json"
    cover_md_path = role_dir / "cover_letter.md"
    resume_pdf_path = role_dir / "resume.pdf"
    cover_pdf_path = role_dir / "cover_letter.pdf"
    report_path = role_dir / "render_report.json"

    warnings = []
    rendered_at = datetime.utcnow().isoformat() + "Z"

    # ── Load resume.json ──
    resume_data = json.loads(resume_json_path.read_text(encoding="utf-8"))

    # ── Build resume HTML ──
    resume_html = build_resume_html(resume_data)

    # ── Render resume to PDF ──
    page.set_content(resume_html, wait_until="networkidle")
    page.wait_for_timeout(300)  # small settle
    page.pdf(
        path=str(resume_pdf_path),
        format="Letter",
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        print_background=True,
    )
    resume_pages = count_pdf_pages(resume_pdf_path)
    resume_size = resume_pdf_path.stat().st_size if resume_pdf_path.exists() else 0

    # ── HARD CHECK: resume must be 1 page ──
    if resume_pages != 1:
        return {
            "blocker": f"1-page resume constraint violated for {role_id}",
            "current_page_count": resume_pages,
            "role_id": role_id,
            "diagnostic": "Resume content exceeded one page. Check bullet count and lengths.",
            "recommendation": "Remove 1-2 bullets from longest experience entries or shorten summary.",
        }

    # ── Render cover letter to PDF ──
    cover_md = cover_md_path.read_text(encoding="utf-8")
    cover_html = build_cover_html(cover_md)
    page.set_content(cover_html, wait_until="networkidle")
    page.wait_for_timeout(200)
    page.pdf(
        path=str(cover_pdf_path),
        format="Letter",
        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        print_background=True,
    )
    cover_pages = count_pdf_pages(cover_pdf_path)
    cover_size = cover_pdf_path.stat().st_size if cover_pdf_path.exists() else 0

    if cover_pages > 1:
        warnings.append(f"Cover letter is {cover_pages} pages (target: 1)")

    # ── Build report ──
    report = {
        "role_id": role_id,
        "resume_pages": resume_pages,
        "cover_pages": cover_pages,
        "resume_size_bytes": resume_size,
        "cover_size_bytes": cover_size,
        "resume_path": str(resume_pdf_path),
        "cover_path": str(cover_pdf_path),
        "rendered_at": rendered_at,
        "warnings": warnings,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  [OK] {role_id}: resume={resume_pages}p cover={cover_pages}p", flush=True)

    # ── Screenshots for Carlos Rosario only ──
    if is_carlos and screenshots_dir:
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Screenshot resume PDF page 1 by rendering the HTML again
        page.set_content(resume_html, wait_until="networkidle")
        page.wait_for_timeout(300)
        # Set viewport to letter size at 96dpi (816x1056 px)
        page.set_viewport_size({"width": 816, "height": 1056})
        resume_png = screenshots_dir / "carlosrosario_resume_preview.png"
        page.screenshot(path=str(resume_png), full_page=False, clip={"x": 0, "y": 0, "width": 816, "height": 1056})

        # Screenshot cover letter
        page.set_content(cover_html, wait_until="networkidle")
        page.wait_for_timeout(200)
        cover_png = screenshots_dir / "carlosrosario_cover_preview.png"
        page.screenshot(path=str(cover_png), full_page=False, clip={"x": 0, "y": 0, "width": 816, "height": 1056})

        report["resume_preview_png"] = str(resume_png)
        report["cover_preview_png"] = str(cover_png)
        # Update report file with screenshot paths
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"  [SCREENSHOTS] saved to {screenshots_dir}", flush=True)

    return report


def main():
    from playwright.sync_api import sync_playwright

    start_time = time.time()
    roles_rendered = 0
    roles_failed = []
    render_reports = []
    carlos_pngs = []
    blocker_result = None

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 816, "height": 1056},
        )
        page = context.new_page()

        for i, role_id in enumerate(ROLES):
            is_carlos = (i == 0)
            print(f"\nRendering [{i+1}/{len(ROLES)}]: {role_id}", flush=True)

            try:
                report = render_role(
                    role_id,
                    page,
                    is_carlos=is_carlos,
                    screenshots_dir=SCREENSHOTS_DIR if is_carlos else None,
                )
            except Exception as e:
                print(f"  [ERROR] {role_id}: {e}", flush=True)
                roles_failed.append({"role_id": role_id, "error": str(e)})
                if is_carlos:
                    blocker_result = {
                        "blocker": f"Carlos Rosario render failed: {e}",
                        "role_id": role_id,
                    }
                continue

            # Check for blocker (1-page violation)
            if "blocker" in report:
                print(f"  [BLOCKER] {report['blocker']}", flush=True)
                if is_carlos:
                    blocker_result = report
                    break  # Stop entirely if Carlos fails
                else:
                    roles_failed.append(report)
                    continue

            render_reports.append(report)
            roles_rendered += 1

            if is_carlos and "resume_preview_png" in report:
                carlos_pngs = [report.get("resume_preview_png", ""), report.get("cover_preview_png", "")]

        browser.close()

    duration = round(time.time() - start_time, 1)

    if blocker_result:
        # Return blocker JSON
        print("\n" + json.dumps(blocker_result, indent=2))
        return

    summary = {
        "agent": "pdf_renderer",
        "tool_used": "playwright",
        "roles_rendered": roles_rendered,
        "roles_failed": roles_failed,
        "render_reports": render_reports,
        "carlosrosario_sample_pngs": carlos_pngs,
        "duration_total_s": duration,
    }
    print("\n" + "=" * 60)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
