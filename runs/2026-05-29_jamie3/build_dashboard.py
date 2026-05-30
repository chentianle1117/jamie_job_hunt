#!/usr/bin/env python3
"""Generate self-contained review dashboard (base64-embedded previews) from state_review.json."""
import json, base64
from pathlib import Path
from html import escape

RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-29_jamie3")
state = json.load(open(RUN/"state_review.json", encoding="utf-8"))

def b64(p):
    p = Path(p)
    if not p.exists(): return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

def fit_color(fit):
    f = fit.lower()
    if f.startswith("go") and "stretch" not in f: return "#16a34a"
    if "stretch" in f and "go" in f: return "#0891b2"
    if "stretch" in f: return "#d97706"
    return "#6b7280"

def card(e, lane):
    rpng, cpng = b64(e["resume_png"]), b64(e["cover_png"])
    picked = " 👁️ Jamie picked" if e.get("jamie_picked") else ""
    rpdf = "file:///" + e["resume_pdf"].replace("\\","/")
    cpdf = "file:///" + e["cover_pdf"].replace("\\","/")
    return f"""
    <div class="card">
      <div class="card-head" onclick="this.parentNode.classList.toggle('open')">
        <div class="ch-left">
          <span class="chev">▶</span>
          <div>
            <div class="ctitle">{escape(e['company'])} — {escape(e['role'])}{picked}</div>
            <div class="cmeta">{escape(e['location'])} · {escape(e['ats'])} · summary noun: <b>{escape(e['summary_noun'])}</b></div>
          </div>
        </div>
        <span class="fit" style="background:{fit_color(e['fit'])}">{escape(e['fit'])}</span>
      </div>
      <div class="card-body">
        <p class="note">{escape(e['note'])}</p>
        <div class="links">
          <a href="{escape(e['apply_url'])}" target="_blank">↗ Job posting</a>
          <a href="{rpdf}" target="_blank">📄 Resume PDF</a>
          <a href="{cpdf}" target="_blank">📄 Cover PDF</a>
        </div>
        <div class="previews">
          <div class="prev"><div class="plabel">Tailored Résumé</div><img src="{rpng}" loading="lazy"></div>
          <div class="prev"><div class="plabel">Cover Letter</div><img src="{cpng}" loading="lazy"></div>
        </div>
      </div>
    </div>"""

def outreach_card(o):
    badge = "#7c3aed" if o.get("contact_type")=="senior_leader" else "#0891b2"
    alum = o.get("alumni_connection","none")
    alum_html = f' · <span style="color:#16a34a">{escape(alum)} alum</span>' if alum and alum.lower()!="none" else ""
    return f"""
    <div class="card">
      <div class="card-head" onclick="this.parentNode.classList.toggle('open')">
        <div class="ch-left">
          <span class="chev">▶</span>
          <div>
            <div class="ctitle">{escape(o['contact_name'])} — <span style="font-weight:500">{escape(o['company'])}</span></div>
            <div class="cmeta">{escape(o['contact_title_current'])} · re: {escape(o['role_applied'])}{alum_html}</div>
          </div>
        </div>
        <span class="fit" style="background:{badge}">{escape(o.get('contact_type','peer'))} · {escape(o.get('confidence','—'))}</span>
      </div>
      <div class="card-body">
        <p class="note">✓ Verified: {escape(o.get('verification_evidence',''))}</p>
        <div class="links">
          <a href="{escape(o['linkedin_url'])}" target="_blank">↗ LinkedIn profile</a>
        </div>
        <div class="email">
          <div class="esubj"><b>Subject:</b> {escape(o['subject'])}</div>
          <pre class="ebody">{escape(o['body'])}</pre>
        </div>
      </div>
    </div>"""

# load outreach drafts if present
outreach = []
op = RUN/"outreach_drafts.json"
if op.exists():
    outreach = json.load(open(op, encoding="utf-8"))
outreach_cards = "".join(outreach_card(o) for o in outreach)

review_cards = "".join(card(e,"REVIEW") for e in state["lanes"]["REVIEW"])
# sort discovered: GO first, then by company
disc = sorted(state["lanes"]["DISCOVERED"], key=lambda e:(0 if e["fit"].lower().startswith("go") else 1, e["company"]))
disc_cards = "".join(card(e,"DISCOVERED") for e in disc)
c = state["counts"]

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jamie — Review Dashboard 2026-05-29</title>
<style>
 :root{{--bg:#f6f7f9;--card:#fff;--border:#e4e7eb;--muted:#6b7280;--ink:#111827;--amber:#d97706;--green:#16a34a}}
 *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.5}}
 .wrap{{max-width:1000px;margin:0 auto;padding:24px 16px 80px}}
 h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--muted);font-size:14px;margin:0 0 20px}}
 .banner{{background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:14px 16px;margin-bottom:24px;font-size:14px}}
 .banner b{{color:#92400e}}
 .lane-title{{font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin:28px 0 12px;display:flex;gap:10px;align-items:center}}
 .lane-title .cnt{{background:#e5e7eb;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:600}}
 .card{{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:10px;overflow:hidden}}
 .card-head{{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;cursor:pointer;gap:12px}}
 .card-head:hover{{background:#fafbfc}}
 .ch-left{{display:flex;gap:10px;align-items:flex-start}}
 .chev{{transition:transform .15s;color:var(--muted);font-size:11px;margin-top:4px}}
 .card.open .chev{{transform:rotate(90deg)}}
 .ctitle{{font-weight:650;font-size:15px}} .cmeta{{font-size:12.5px;color:var(--muted);margin-top:2px}}
 .fit{{color:#fff;font-size:11px;font-weight:600;padding:3px 9px;border-radius:10px;white-space:nowrap}}
 .card-body{{display:none;padding:0 16px 18px;border-top:1px solid var(--border)}}
 .card.open .card-body{{display:block}}
 .note{{font-size:13.5px;background:#f9fafb;border-left:3px solid var(--amber);padding:10px 12px;border-radius:4px;margin:14px 0}}
 .links{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:14px}}
 .links a{{font-size:13px;text-decoration:none;color:#2563eb;font-weight:500}}
 .links a:hover{{text-decoration:underline}}
 .previews{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
 @media(max-width:680px){{.previews{{grid-template-columns:1fr}}}}
 .prev{{border:1px solid var(--border);border-radius:8px;overflow:hidden;background:#fff}}
 .plabel{{font-size:11px;font-weight:600;color:var(--muted);padding:6px 10px;background:#f9fafb;border-bottom:1px solid var(--border)}}
 .prev img{{width:100%;display:block}}
 .email{{border:1px solid var(--border);border-radius:8px;overflow:hidden}}
 .esubj{{font-size:13px;padding:8px 12px;background:#f9fafb;border-bottom:1px solid var(--border)}}
 .ebody{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:13px;white-space:pre-wrap;word-wrap:break-word;margin:0;padding:12px;line-height:1.55}}
</style></head><body><div class="wrap">
 <h1>Jamie — Application Review Dashboard</h1>
 <p class="sub">Run 2026-05-29 · {c['total']} tailored packages · {len(outreach)} verified outreach drafts · every résumé + cover built to Jamie's latest feedback rules</p>
 <div class="banner">
   <b>⏸ Nothing has been submitted.</b> These are tailored drafts for your review. The first three (👁️ <b>your picks</b> — Axon, Accuris, Chartis) are here so you can confirm today's feedback was correctly baked into the pipeline. The other {c['discovered']} were auto-discovered as fitting roles (People + Product/Program PM). Click any card to expand the résumé + cover preview. Once you confirm the quality looks right, tell David and the pipeline will submit the ones you approve.
 </div>

 <div class="lane-title">👁️ Your Picks — Confirm Feedback Incorporation <span class="cnt">{c['review']}</span></div>
 {review_cards}

 <div class="lane-title">🔎 Auto-Discovered Fitting Roles <span class="cnt">{c['discovered']}</span></div>
 {disc_cards}

 <div class="lane-title">📧 Outreach Drafts — Review Before Sending <span class="cnt">{len(outreach)}</span></div>
 <div class="banner" style="background:#ede9fe;border-color:#c4b5fd">Every contact below was <b>verified currently employed</b> via live LinkedIn (one who'd left was dropped). Click to read the full draft email. <b>Nothing has been sent</b> — these are for Jamie to review, edit, and send herself. Axon is prioritized per Jamie's request.</div>
 {outreach_cards}
</div></body></html>"""

out = RUN/"dashboard_review.html"
out.write_text(html, encoding="utf-8")
print("Dashboard written:", out, f"({len(html)//1024} KB)")
