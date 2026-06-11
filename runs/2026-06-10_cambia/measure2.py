#!/usr/bin/env python3
"""Measure actual page height with current settings — fine tune."""
import json, re
from pathlib import Path

REPO = Path("/Users/jamiecheng/jamie_job_hunt")
JSON_PATH = REPO / "tailored_resumes" / "Cambia_Jamie (Yi-Chieh) Cheng_Community-Culture-Program-Manager_2026-06-10.json"

def expand_kw(text):
    return re.sub(r'\{(\w+)\|([^}]+)\}', r'\2', text) if text else ""

def build_resume_html(data, margins, jm=6, sm="3pt 0", shm="5pt 0 2pt 0"):
    top, right, bottom, left = margins
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
        title_extra = f' <a class="work-sample" href="{ws_url}" target="_blank">(Work Sample)</a>' if ws_url else ""
        bullets_html = "".join(f"<li>&bull; {expand_kw(b.get('text','') if isinstance(b,dict) else b)}</li>\n" for b in bullets)
        exp_html += f'<div class="job"><div class="job-title-row"><div class="job-title">{title}{title_extra}</div><div class="job-location">{location}</div></div><div class="job-company-row"><div class="job-company">{company}</div><div class="job-dates">{dates}</div></div><ul>{bullets_html}</ul></div>'
    edu_html = ""
    for edu in education:
        eb = "".join(f"<li>&bull; {b}</li>\n" for b in edu.get("bullets",[]))
        bb = f"<ul>{eb}</ul>" if eb else ""
        edu_html += f'<div class="edu"><div class="edu-row"><div class="edu-school">{edu.get("school","")}</div><div class="edu-location">{edu.get("location","")}</div></div><div class="edu-row"><div class="edu-degree">{edu.get("degree","")}</div><div class="edu-dates">{edu.get("dates","")}</div></div>{bb}</div>'
    proj_html = "".join(f"<li>{p}</li>" for p in projects)
    skills_html = "".join(f"<li>{expand_kw(s)}</li>" for s in skills)
    loc = header.get("location","Portland, OR (Open to Remote or Relocation)")
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
:root{{--body-font-size:9.5pt;--bullet-font-size:9.2pt;--summary-font-size:9pt;
--header-name-size:19pt;--header-contact-size:8.8pt;--section-header-size:9pt;
--job-title-size:9.5pt;--work-sample-size:7.5pt;
--body-line-height:1.15;--bullet-line-height:1.25;--summary-line-height:1.28;
--summary-margin:{sm};--section-header-margin:{shm};
--job-margin-bottom:{jm}pt;--edu-margin-bottom:5pt;--edu-ul-margin-top:2pt;
--accent-color:#2a6496;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Calibri','Helvetica Neue','Arial',sans-serif;font-size:var(--body-font-size);
line-height:var(--body-line-height);color:#1a1a1a;padding:{top} {right} {bottom} {left};}}
.header{{text-align:center;margin-bottom:2pt;}}
.header h1{{font-size:var(--header-name-size);font-weight:bold;letter-spacing:0.3pt;margin-bottom:5pt;}}
.header .contact{{font-size:var(--header-contact-size);color:#333;}}
.header .contact a{{color:var(--accent-color);text-decoration:underline;}}
.summary{{padding:4pt 7pt;margin:var(--summary-margin);font-size:var(--summary-font-size);
line-height:var(--summary-line-height);font-style:italic;color:#222;text-align:center;}}
.section-header{{text-align:center;font-size:var(--section-header-size);font-weight:bold;
letter-spacing:0.8pt;text-transform:uppercase;border-bottom:1px solid #000;
padding:1pt 0;margin:var(--section-header-margin);}}
.job{{margin-bottom:var(--job-margin-bottom);}}
.job-title-row{{display:flex;justify-content:space-between;align-items:baseline;}}
.job-title{{font-weight:bold;font-size:var(--job-title-size);}}
.job-title a.work-sample{{font-weight:normal;font-size:var(--work-sample-size);text-decoration:underline;color:var(--accent-color);}}
.job-location{{font-size:var(--job-title-size);text-align:right;white-space:nowrap;}}
.job-company-row{{display:flex;justify-content:space-between;align-items:baseline;}}
.job-company{{color:var(--accent-color);font-size:var(--job-title-size);}}
.job-dates{{font-style:italic;font-size:var(--job-title-size);text-align:right;white-space:nowrap;color:var(--accent-color);}}
.job ul{{margin:2pt 0 0 8pt;padding:0;list-style:none;}}
.job li{{font-size:var(--bullet-font-size);line-height:var(--bullet-line-height);margin-bottom:0.5pt;padding-left:1pt;}}
.edu{{margin-bottom:var(--edu-margin-bottom);}}
.edu-row{{display:flex;justify-content:space-between;align-items:baseline;}}
.edu-school{{font-weight:bold;font-size:var(--job-title-size);}}
.edu-location{{font-size:var(--job-title-size);text-align:right;}}
.edu-degree{{font-size:var(--job-title-size);}}
.edu-dates{{font-style:italic;font-size:var(--job-title-size);text-align:right;color:var(--accent-color);}}
.edu ul{{margin:var(--edu-ul-margin-top) 0 0 12pt;padding:0;list-style:none;}}
.edu li{{font-size:var(--bullet-font-size);line-height:1.35;}}
.simple-list{{margin:0;padding:0;list-style:none;}}
.simple-list li{{font-size:var(--bullet-font-size);line-height:1.38;margin-bottom:1.5pt;}}
</style></head><body>
<div class="header"><h1>Jamie (Yi-Chieh) Cheng</h1>
<div class="contact">{loc} &bull; (213) 700-3831 &bull;
<a href="mailto:jamiecheng0103@gmail.com">jamiecheng0103@gmail.com</a> &bull;
<a href="http://www.linkedin.com/in/jamieyccheng">LinkedIn</a></div></div>
<div class="summary">{summary}</div>
<div class="section-header">Professional Experience</div>{exp_html}
<div class="section-header">Education</div>{edu_html}
<div class="section-header">Projects &amp; Awards</div><ul class="simple-list">{proj_html}</ul>
<div class="section-header">Skills</div><ul class="simple-list">{skills_html}</ul>
</body></html>"""

from playwright.sync_api import sync_playwright
data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

tests = [
    (("0.25in","0.40in","0.25in","0.40in"), 6, "3pt 0", "5pt 0 2pt 0"),
    (("0.22in","0.40in","0.22in","0.40in"), 6, "3pt 0", "5pt 0 2pt 0"),
    (("0.22in","0.40in","0.22in","0.40in"), 5, "2pt 0", "4pt 0 2pt 0"),
    (("0.20in","0.40in","0.20in","0.40in"), 5, "2pt 0", "4pt 0 2pt 0"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 816, "height": 1056})
    page = ctx.new_page()
    for margins, jm, sm, shm in tests:
        html = build_resume_html(data, margins, jm, sm, shm)
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(200)
        h = page.evaluate("document.body.scrollHeight")
        status = "OK" if h <= 1056 else f"OVER by {h-1056}px"
        print(f"m={margins[0]}/{margins[2]} jm={jm}pt sm={sm} shm={shm[:5]}: h={h} {status}")
    browser.close()
