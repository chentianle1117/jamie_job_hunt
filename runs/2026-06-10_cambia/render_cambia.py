#!/usr/bin/env python3
"""Render Cambia resume JSON -> PDF + PNG preview (Mac/local renderer)."""
import json, sys, re
from pathlib import Path

REPO = Path("/Users/jamiecheng/jamie_job_hunt")
JSON_NAME = "Cambia_Jamie (Yi-Chieh) Cheng_Community-Culture-Program-Manager_2026-06-10"
JSON_PATH = REPO / "tailored_resumes" / f"{JSON_NAME}.json"
PDF_PATH  = REPO / "tailored_resumes" / f"{JSON_NAME}.pdf"
RUN_DIR   = REPO / "runs" / "2026-06-10_cambia"
RUN_PDF   = RUN_DIR / "resume.pdf"
RUN_PNG   = RUN_DIR / "resume_preview.png"

def expand_kw(text):
    if not text:
        return ""
    return re.sub(r'\{(\w+)\|([^}]+)\}', r'\2', text)

def build_resume_html(data):
    meta = data.get("meta", {})
    margins = meta.get("pageMargins", {})
    top = margins.get("top", "0.35in")
    right = margins.get("right", "0.45in")
    bottom = margins.get("bottom", "0.35in")
    left = margins.get("left", "0.45in")

    header = data.get("header", {})
    summary = expand_kw(data.get("summary", ""))
    experience = data.get("experience", [])
    education = data.get("education", [])
    projects = data.get("projects", [])
    skills = data.get("skills", [])

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

    proj_html = ""
    for p in projects:
        proj_html += f"<li>{p}</li>\n"

    skills_html = ""
    for s in skills:
        skills_html += f"<li>{expand_kw(s)}</li>\n"

    loc = header.get("location", "Portland, OR (Open to Remote or Relocation)")

    return f"""<!DOCTYPE html>
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
    --body-line-height: 1.15;
    --bullet-line-height: 1.25;
    --summary-line-height: 1.28;
    --summary-margin: 3pt 0;
    --section-header-margin: 5pt 0 2pt 0;
    --job-margin-bottom: 6pt;
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
  .kw, .jd-kw {{ padding: 0 !important; }}
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


def main():
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    html = build_resume_html(data)

    RUN_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 816, "height": 1056})
        page = ctx.new_page()

        # Render PDF
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(300)
        page.pdf(
            path=str(PDF_PATH),
            format="Letter",
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            print_background=True,
        )
        print(f"[PDF] Written to {PDF_PATH}", flush=True)

        # Count pages
        reader = PdfReader(str(PDF_PATH))
        page_count = len(reader.pages)
        print(f"[PAGES] {page_count}", flush=True)

        # Hard check
        if page_count != 1:
            print(f"[BLOCKER] Resume is {page_count} pages — must be 1!", flush=True)
            browser.close()
            sys.exit(1)

        # Copy to runs dir
        import shutil
        shutil.copy(str(PDF_PATH), str(RUN_PDF))
        print(f"[COPY] {RUN_PDF}", flush=True)

        # PNG preview
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(300)
        page.set_viewport_size({"width": 816, "height": 1056})
        page.screenshot(
            path=str(RUN_PNG),
            clip={"x": 0, "y": 0, "width": 816, "height": 1056}
        )
        print(f"[PNG] {RUN_PNG}", flush=True)

        browser.close()

    print("[DONE]")


if __name__ == "__main__":
    main()
