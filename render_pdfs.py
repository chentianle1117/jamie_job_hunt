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


def build_cover_html(md_content, location=None):
    """Convert cover letter markdown to Jamie's CANONICAL 2-column cover format.

    `location` (optional): the role's header location string (e.g.
    "Seattle, WA (Open to Hybrid or Relocation)"). Used to render the sidebar
    city line so the cover matches the resume header per role — NOT hardcoded to
    Portland (2026-06-13 fix: sidebar location was previously always "Portland, OR",
    ignoring the target role's city).

    Canonical reference: jamie/cover_letter_template.html (from RRD_..._2026-05-12.html).
    Layout: cream header band (name + 2-line tagline) → 2-column body (left sidebar
    with contact, right justified letter). "Dear [Company] Hiring Team," salutation.
    Bold keywords preserved. Cursive signature + printed name.

    Expected md structure (flexible parser):
        # Cover Letter — Company
        ## Role Title
        **Jamie (Yi-Chieh) Cheng** | jamiecheng0103@gmail.com | Portland, OR   (header line — skipped)
        A Solution-focused, Data-driven, and People-oriented Professional       (tagline line 1)
        Dedicated to Improving People Experience                                (tagline line 2)
        ---
        May 27, 2026                                                            (date)
        Dear [Company] Hiring Team,    (or "Hiring Manager / Company / City" block — we take the Dear line)
        ---
        <body paragraphs>
        Sincerely,
        Jamie (Yi-Chieh) Cheng
    """
    DEFAULT_TAGLINE_1 = "A Solution-focused, Data-driven, and People-oriented Professional"
    DEFAULT_TAGLINE_2 = "Dedicated to Improving People Experience"

    lines = md_content.strip().split("\n")

    tagline1 = DEFAULT_TAGLINE_1
    tagline2 = DEFAULT_TAGLINE_2
    date_str = ""
    salutation = "Dear Hiring Team,"
    body_paras = []
    closing = "Sincerely,"
    sig_name = "Jamie (Yi-Chieh) Cheng"

    rule_count = 0
    seen_tagline1 = False
    collecting_body = False

    for raw in lines:
        s = raw.strip()
        if not s:
            continue

        # H1/H2 markdown headers — skip (company/role meta)
        if s.startswith("#"):
            continue

        # Horizontal rule = section divider
        if s == "---":
            rule_count += 1
            if rule_count >= 2:
                collecting_body = True
            continue

        # Header identity line: "**Jamie...** | email | loc" — skip
        if s.startswith("**") and ("|" in s or "Cheng" in s) and not collecting_body:
            continue

        # Before first rule: capture taglines
        if rule_count == 0:
            # Strip markdown emphasis wrappers (*italic* / **bold**) — the cream header
            # already styles these; raw asterisks must NEVER show in the PDF (2026-06-12 fix).
            def _clean_tagline(t):
                t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)   # **bold**
                t = re.sub(r'\*(.+?)\*', r'\1', t)        # *italic*
                return t.strip('* ').strip()
            # Tagline lines = the two descriptor lines under the name, BEFORE the first ---.
            # Capture STRUCTURALLY (1st such line -> tagline1, 2nd -> tagline2) rather than by
            # keyword, so custom taglines per role render correctly (2026-06-12 fix: previously
            # only the hardcoded "Solution-focused"/"Dedicated to" phrasing was honored, silently
            # falling back to defaults for any other tagline).
            cleaned = _clean_tagline(s)
            if not cleaned:
                continue
            if not seen_tagline1:
                tagline1 = cleaned
                seen_tagline1 = True
            else:
                tagline2 = cleaned
            continue

        # Between rule 1 and rule 2: date + salutation block.
        # ROBUSTNESS FIX (2026-06-12): the salutation ("Dear ...,") marks the start of the
        # body even if there is NO second `---` rule. Previously, with only one `---`, body
        # paragraphs fell through here and were SILENTLY DROPPED (the empty-cover bug).
        if rule_count == 1 and not collecting_body:
            low = s.lower()
            if s.startswith("Dear") or low.startswith("dear"):
                salutation = s
                collecting_body = True   # everything AFTER the salutation is body
                continue
            # Date line (contains a year or month)
            if re.search(r'(19|20)\d{2}', s) and not s.startswith("Dear"):
                # Skip company-name / city address lines; only take the date
                if re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|\d{1,2}[/-]\d)', s):
                    date_str = s
                continue
            # Contact sidebar line (phone · city · email · LinkedIn) before the date — skip
            continue

        # Body region
        if collecting_body:
            low = s.lower()
            if low.startswith("sincerely") or low.startswith("warm") or low.startswith("best") or low.startswith("regards"):
                closing = s.rstrip(",") + ","
                continue
            # Name after closing
            if "Cheng" in s and len(s) < 40:
                sig_name = s
                continue
            # Skip any leftover tone-note / bracket lines
            if s.startswith("[") or s.startswith("TONE") or s.startswith("Why this"):
                continue
            # Body paragraph — convert **bold**
            formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            body_paras.append(f"<p>{formatted}</p>")

    body_html = "\n    ".join(body_paras)

    # ── Sidebar location lines (per-role, not hardcoded) ──
    # Default mirrors the canonical template; override from the role's header location.
    sidebar_city = "Portland, OR"
    sidebar_paren = "(Open to Remote or Relocation)"
    if location:
        loc = location.strip()
        m = re.match(r'^(.*?)\s*(\([^)]*\))\s*$', loc)
        if m:
            sidebar_city = m.group(1).strip()
            sidebar_paren = m.group(2).strip()
        else:
            sidebar_city = loc
            sidebar_paren = ""
    sidebar_loc_html = sidebar_city + "<br>"
    if sidebar_paren:
        sidebar_loc_html += sidebar_paren + "<br>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: letter; margin: 0.3in 0 0.3in 0; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Calibri','Arial',sans-serif; font-size: 11pt; color: #1a1a1a;
          -webkit-print-color-adjust: exact; print-color-adjust: exact; }}

  .header {{ background: #f5ede0; text-align: center; padding: 12pt 40pt 10pt 40pt; }}
  .header h1 {{ font-size: 26pt; font-weight: bold; letter-spacing: 0.5pt; margin-bottom: 4pt; }}
  .header .subtitle {{ font-size: 10.5pt; font-weight: bold; line-height: 1.4; }}

  .body-wrap {{ display: flex; min-height: calc(100vh - 120pt); }}
  .sidebar {{ width: 145pt; flex-shrink: 0; padding: 16pt 10pt 16pt 14pt;
              font-size: 9pt; line-height: 1.55; border-right: 1px solid #ccc; color: #333; }}
  .sidebar a {{ color: #2a6496; text-decoration: underline; }}

  .letter {{ flex: 1; padding: 16pt 22pt 16pt 16pt; font-size: 10pt; line-height: 1.44; }}
  .letter .date {{ margin-bottom: 8pt; }}
  .letter .salutation {{ margin-bottom: 8pt; }}
  .letter p {{ margin-bottom: 7pt; text-align: justify; }}
  .letter .closing {{ margin-top: 8pt; margin-bottom: 3pt; }}
  .letter .sig-script {{ font-family: 'Brush Script MT','Segoe Script',cursive; font-size: 18pt; margin: 4pt 0 2pt 0; color: #1a1a1a; }}
  .letter .sig-name {{ font-size: 10.8pt; }}
  strong {{ font-weight: bold; }}

  @media print {{ body {{ background: white; }} .body-wrap {{ min-height: auto; }} }}
</style>
</head>
<body>

<div class="header">
  <h1>Jamie Cheng</h1>
  <div class="subtitle">
    {tagline1}<br>
    {tagline2}
  </div>
</div>

<div class="body-wrap">
  <div class="sidebar">
    213-700-3831<br>
    {sidebar_loc_html}
    <a href="mailto:jamiecheng0103@gmail.com">jamiecheng0103@gmail.com</a><br>
    <a href="http://www.linkedin.com/in/jamieyccheng">LinkedIn</a>
  </div>

  <div class="letter">
    <div class="date">{date_str}</div>
    <div class="salutation">{salutation}</div>

    {body_html}

    <div class="closing">{closing}</div>
    <div class="sig-script">Jamie Cheng</div>
    <div class="sig-name">{sig_name}</div>
  </div>
</div>
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
    cover_html = build_cover_html(cover_md, location=resume_data.get("header", {}).get("location"))

    # ── CONTENT GATE (2026-06-12): block the silent empty-cover bug ──
    # A real cover has 3-5 body <p> paragraphs. If the parser produced <3, the markdown
    # structure didn't match and the body was dropped — FAIL loudly, never ship a blank cover.
    cover_para_count = cover_html.count("<p>")
    if cover_para_count < 3:
        return {
            "blocker": f"Cover letter body has only {cover_para_count} paragraph(s) for {role_id} — likely a parse/drop failure",
            "role_id": role_id,
            "diagnostic": "build_cover_html() did not capture the body paragraphs. Check the cover_letter.md "
                          "structure (needs a 'Dear ...,' salutation line; body follows it).",
            "recommendation": "Verify cover_letter.md has real body paragraphs after the salutation; re-render.",
        }

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
