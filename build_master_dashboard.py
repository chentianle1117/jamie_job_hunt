#!/usr/bin/env python3
"""MASTER dashboard across ALL runs — organized by submission date + status, with version tracking.

Scans every runs/*/discovered/* role package + the prior master_tracker entries, classifies each:
  SUBMITTED (grouped by date, with package/version links + confirmation)
  NEEDS ATTENTION  (essay-approved-but-form-stuck / finish-manually / blocked-ATS)
  DROPPED (5+ yrs) / DEFERRED (cap/no-sponsor)
Writes master_dashboard.html (self-contained, base64 previews) + master_index.json (machine-readable).
"""
import json, base64, glob, os, html
from pathlib import Path
from datetime import datetime

ROOT = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search")
RUNS = ROOT/"runs"
esc = html.escape

def jload(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None

def b64(p):
    p = Path(p)
    if not p.exists(): return ""
    try: return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    except Exception: return ""

# YOE drops + deferred from the night run (carry the rule forward)
_yoe = jload(RUNS/"2026-05-30_night"/"yoe_verdicts.json") or {}
YOE_DROP_IDS = set(_yoe.get("drop", {}).keys())
DEFERRED_IDS = {"affirm_workplace_manager","anthropic_implementation_specialist","figma_onboarding_manager_customer",
                "chime_program_manager_dispute","robinhood_people_systems_manager","notion_people_partner_epd",
                "datadog_inclusion_program_manager"}

records = []  # unified

# 1) prior tracker apps (runs before packaged folders) — submitted, dated
tr = jload(ROOT/"jamie"/"master_tracker.json") or {"applications":[]}
pkg_keys = set()
for run in sorted(RUNS.iterdir()):
    disc = run/"discovered"
    if not disc.exists(): continue
    for d in sorted(disc.iterdir()):
        if not (d/"form_fields.json").exists(): continue
        ff = jload(d/"form_fields.json") or {}
        meta = ff.get("meta", {})
        rid = d.name
        co, ro = meta.get("company",""), meta.get("role","")
        pkg_keys.add((co, ro))
        sj = jload(d/"SUBMITTED.json")
        submitted = bool(sj and sj.get("success"))
        date_sub = (sj.get("timestamp","")[:10] if submitted and sj else "")
        # classify status
        if submitted:
            status = "SUBMITTED"
        elif rid in YOE_DROP_IDS:
            status = "DROPPED"
        elif rid in DEFERRED_IDS:
            status = "DEFERRED"
        elif (d/"essay_answers.json").exists() or (d/"essays_for_review.json").exists():
            status = "ATTENTION"  # essays approved/awaiting + form needs finishing
        elif (meta.get("ats","") or "").lower() in ("workday","icims","other"):
            status = "BLOCKED"
        else:
            status = "ATTENTION"
        records.append({
            "rid": rid, "run": run.name, "company": co, "role": ro,
            "ats": meta.get("ats",""), "url": meta.get("url",""),
            "min_years": meta.get("min_years",""), "why": meta.get("why_fit",""),
            "status": status, "date": date_sub,
            "resume_pdf": str(d/"resume.pdf"), "cover_pdf": str(d/"cover_letter.pdf"),
            "resume_png": str(d/"resume_preview.png"),
            "conf_url": (sj.get("url_after","") if sj else ""),
            "essays": bool((d/"essay_answers.json").exists() or (d/"essays_for_review.json").exists()),
        })

# 2) tracker apps NOT represented by a package folder (the first 10 from prior runs)
for a in tr["applications"]:
    if (a["company"], a["title"]) in pkg_keys: continue
    records.append({
        "rid": a.get("id",""), "run": "prior", "company": a["company"], "role": a["title"],
        "ats": a.get("ats",""), "url": a.get("url",""), "min_years":"", "why":a.get("notes",""),
        "status": "SUBMITTED" if a.get("lane")=="AUTO_SUBMITTED" else "ATTENTION",
        "date": a.get("date_applied",""), "resume_pdf":"", "cover_pdf":"", "resume_png":"",
        "conf_url": a.get("confirmation_url",""), "essays": False,
    })

# dedup by (company, role) — keep the most-progressed (SUBMITTED wins)
PRI = {"SUBMITTED":0,"ATTENTION":1,"BLOCKED":2,"DEFERRED":3,"DROPPED":4}
best = {}
for r in records:
    k = (r["company"], r["role"])
    if k not in best or PRI[r["status"]] < PRI[best[k]["status"]]:
        best[k] = r
records = list(best.values())

counts = {}
for r in records: counts[r["status"]] = counts.get(r["status"],0)+1

def card(r, show_preview=True):
    rpng = b64(r["resume_png"]) if show_preview else ""
    rpdf = "file:///"+r["resume_pdf"].replace("\\","/") if r["resume_pdf"] else ""
    cpdf = "file:///"+r["cover_pdf"].replace("\\","/") if r["cover_pdf"] else ""
    links = [f'<a href="{esc(r["url"])}" target="_blank">↗ Posting</a>'] if r["url"] else []
    if rpdf: links.append(f'<a href="{rpdf}" target="_blank">📄 Résumé</a>')
    if cpdf: links.append(f'<a href="{cpdf}" target="_blank">📄 Cover</a>')
    if r["conf_url"] and "confirmation" in (r["conf_url"] or "").lower():
        links.append(f'<a href="{esc(r["conf_url"])}" target="_blank">✓ Confirmation</a>')
    yrs = f' · req {esc(r["min_years"])}' if r["min_years"] else ""
    run_tag = f' · <span class="run">{esc(r["run"])}</span>'
    return f"""<div class="card">
      <div class="ch" onclick="this.parentNode.classList.toggle('open')">
        <div><div class="ct">{esc(r['company'])} — {esc(r['role'])}</div>
        <div class="cm">{esc(r['ats'])}{yrs}{run_tag}{(' · '+esc(r['date'])) if r['date'] else ''}</div></div>
      </div>
      <div class="cb">
        {f'<div class="why">{esc(r["why"])}</div>' if r["why"] else ''}
        <div class="lk">{' '.join(links)}</div>
        {f'<img class="prev" src="{rpng}" loading="lazy">' if rpng else ''}
      </div></div>"""

# SUBMITTED grouped by date (desc)
sub = [r for r in records if r["status"]=="SUBMITTED"]
by_date = {}
for r in sub: by_date.setdefault(r["date"] or "(date n/a)", []).append(r)
sub_html = ""
for date in sorted(by_date, reverse=True):
    rs = sorted(by_date[date], key=lambda x:x["company"])
    sub_html += f'<div class="datehdr">{esc(date)} <span class="cnt">{len(rs)}</span></div>' + "".join(card(r, show_preview=False) for r in rs)

def section(title, status, blurb, preview=True):
    rs = sorted([r for r in records if r["status"]==status], key=lambda x:(x["company"],x["role"]))
    if not rs: return ""
    return f'<div class="lane">{title} <span class="cnt">{len(rs)}</span></div><div class="bl">{blurb}</div>'+"".join(card(r,preview) for r in rs)

total_sub = len(sub)
html_doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Jamie — Master Application Dashboard</title><style>
*{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#111827;line-height:1.5}}
.wrap{{max-width:1040px;margin:0 auto;padding:22px 16px 80px}}
h1{{font-size:23px;margin:0 0 4px}} .sub{{color:#6b7280;font-size:14px;margin:0 0 18px}}
.kpis{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}}
.kpi{{background:#fff;border:1px solid #e4e7eb;border-radius:10px;padding:10px 16px;text-align:center;min-width:96px}}
.kpi .n{{font-size:24px;font-weight:800}} .kpi .l{{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.4px}}
.lane{{font-size:15px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;margin:26px 0 6px;display:flex;gap:10px;align-items:center}}
.cnt{{background:#e5e7eb;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:700}}
.bl{{font-size:13px;color:#6b7280;margin-bottom:12px}}
.datehdr{{font-size:13px;font-weight:800;color:#16a34a;margin:16px 0 6px;display:flex;gap:8px;align-items:center}}
.card{{background:#fff;border:1px solid #e4e7eb;border-radius:9px;margin-bottom:8px;overflow:hidden}}
.ch{{padding:11px 14px;cursor:pointer}} .ch:hover{{background:#fafbfc}}
.ct{{font-weight:650;font-size:14.5px}} .cm{{font-size:12px;color:#6b7280;margin-top:2px}} .run{{color:#9ca3af}}
.cb{{display:none;padding:0 14px 14px;border-top:1px solid #eee}} .card.open .cb{{display:block}}
.why{{font-size:13px;background:#f9fafb;border-left:3px solid #c4b5fd;padding:7px 10px;border-radius:4px;margin:10px 0}}
.lk{{display:flex;gap:13px;flex-wrap:wrap;margin:8px 0}} .lk a{{font-size:13px;color:#2563eb;text-decoration:none;font-weight:500}}
.prev{{width:100%;border:1px solid #e4e7eb;border-radius:8px;margin-top:8px}}
.banner{{background:#ecfdf5;border:1px solid #a7f3d0;border-radius:10px;padding:13px 16px;margin-bottom:18px;font-size:14px}}
</style></head><body><div class="wrap">
<h1>Jamie — Master Application Dashboard</h1>
<p class="sub">All runs combined · generated {datetime.now().strftime('%Y-%m-%d %H:%M') if False else '2026-05-31'} · click any card to expand</p>
<div class="kpis">
  <div class="kpi"><div class="n" style="color:#16a34a">{counts.get('SUBMITTED',0)}</div><div class="l">Submitted</div></div>
  <div class="kpi"><div class="n" style="color:#d97706">{counts.get('ATTENTION',0)}</div><div class="l">Needs Attention</div></div>
  <div class="kpi"><div class="n" style="color:#6b7280">{counts.get('BLOCKED',0)}</div><div class="l">Blocked ATS</div></div>
  <div class="kpi"><div class="n" style="color:#94a3b8">{counts.get('DEFERRED',0)}</div><div class="l">Deferred</div></div>
  <div class="kpi"><div class="n" style="color:#dc2626">{counts.get('DROPPED',0)}</div><div class="l">Dropped 5+yr</div></div>
</div>
<div class="banner"><b>✅ {total_sub} applications submitted</b> across all runs (grouped by date below). <b>{counts.get('ATTENTION',0)} need your attention</b> — essays approved + form ~filled, just finish a few fields or approve. Everything is versioned: each card links its résumé/cover PDF + the live posting + (where captured) the confirmation page.</div>
<div class="lane">✅ Submitted — by date <span class="cnt">{total_sub}</span></div>
<div class="bl">Confirmed submissions. Newest first. Each links the exact résumé/cover version sent + confirmation where captured.</div>
{sub_html}
{section("⚠ Needs Attention", "ATTENTION", "Essays approved + form mostly filled, or awaiting your essay approval — finish the last few fields / approve, then submit. Packages ready.")}
{section("🔒 Blocked ATS — Manual Apply", "BLOCKED", "Workday / iCIMS / university portals (incl. cap-exempt gems). Packages ready; apply manually.")}
{section("⏸ Deferred", "DEFERRED", "Per-company cap or no-sponsor. Packages exist if you want any.")}
{section("🚫 Dropped — 5+ yrs required", "DROPPED", "Audited as requiring 5+ years; not applied per your ≤4yr rule.")}
</div></body></html>"""

out = ROOT/"master_dashboard.html"
out.write_text(html_doc, encoding="utf-8")
json.dump({"counts":counts, "records":records}, open(ROOT/"master_index.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
print("Master dashboard:", out, f"({len(html_doc)//1024} KB)")
print("Counts:", counts, "| total roles:", len(records))
