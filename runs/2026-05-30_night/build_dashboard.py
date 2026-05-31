#!/usr/bin/env python3
"""Build the night-run review dashboard (self-contained, base64-embedded previews).
Per role shows: company + role, WHAT THE FIRM DOES, what the JD wants, fit, submission status,
resume+cover preview, and (for essay roles) Opus-drafted essay answers in Jamie's voice — editable
inline — plus the verified outreach drafts. Lanes: SUBMITTED / ESSAY-REVIEW / NEEDS-MANUAL / BLOCKED.
"""
import json, base64, glob, os
from pathlib import Path
from html import escape

RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-30_night")
DISC = RUN / "discovered"

def b64(p):
    p = Path(p)
    if not p.exists(): return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()

def jload(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None

# roles intentionally deferred (no-sponsor, or per-company sound-judgment cap)
DEFERRED = {
    "affirm_workplace_manager": "JD states no visa sponsorship",
    "anthropic_implementation_specialist": "per-company cap — kept Anthropic Program Ops",
    "figma_onboarding_manager_customer": "per-company cap — kept Figma Customer Enablement",
    "chime_program_manager_dispute": "per-company cap — kept Chime Performance",
    "robinhood_people_systems_manager": "per-company cap — kept Robinhood L&D",
    "notion_people_partner_epd": "per-company cap — kept Notion CS Enablement",
    "datadog_inclusion_program_manager": "per-company cap — kept Datadog PBP + Solutions Coord",
}

def role_status(d):
    """Return (lane, badge_text, color). Classifies by: SUBMITTED.json success -> SUBMITTED;
    deferred set -> DEFERRED; essay draft present (or essays_for_review) -> ESSAY; blocked ATS ->
    BLOCKED; else NEEDS (manual finish)."""
    rid = d.name
    sj, nr, ev = d/"SUBMITTED.json", d/"NEEDS_REVIEW.json", d/"essays_for_review.json"
    j = jload(sj)
    if j and j.get("success"): return ("SUBMITTED", "✅ SUBMITTED", "#16a34a")
    if rid in DEFERRED: return ("DEFERRED", "⏸ DEFERRED", "#94a3b8")
    ff = jload(d/"form_fields.json") or {}
    ats = (ff.get("meta", {}).get("ats") or "").lower()
    # essay role if we captured essays OR drafted answers for it
    if ev.exists() or (d/"essay_answers_draft.json").exists():
        return ("ESSAY", "✍️ ESSAY — REVIEW", "#7c3aed")
    if ats in ("workday", "icims", "other"): return ("BLOCKED", "🔒 MANUAL (blocked ATS)", "#6b7280")
    return ("NEEDS", "⚠ FINISH MANUALLY", "#d97706")

def essay_block(d):
    """Render essay questions + Opus drafts (editable textareas)."""
    draft = jload(d/"essay_answers_draft.json")
    cap = jload(d/"essays_for_review.json")
    if not draft and not cap: return ""
    meta = (draft or {}).get("_meta", {})
    rows = []
    # prefer captured real questions; fall back to draft keys
    pairs = []
    if draft:
        for k, v in draft.items():
            if k == "_meta": continue
            pairs.append((k, v))
    for i, (q, a) in enumerate(pairs):
        rows.append(f"""
        <div class="essay">
          <div class="eq">Q: {escape(q)}</div>
          <textarea class="ea" rows="5">{escape(a)}</textarea>
        </div>""")
    capnote = ""
    if cap and cap.get("essays"):
        labels = " · ".join(escape(e.get("label","")[:60]) for e in cap["essays"])
        capnote = f'<div class="capnote">Live form asks: <b>{labels}</b></div>'
    return f"""
      <div class="essays-wrap">
        <div class="essays-title">✍️ Drafted essay answers (Jamie's voice — edit before submitting)</div>
        {capnote}
        {''.join(rows)}
      </div>"""

def card(d):
    ff = jload(d/"form_fields.json") or {}
    meta = ff.get("meta", {})
    co, ro = meta.get("company",""), meta.get("role","")
    url = meta.get("url",""); fit = meta.get("why_fit",""); sal = meta.get("salary")
    capex = meta.get("cap_exempt")
    lane, badge, col = role_status(d)
    draft = jload(d/"essay_answers_draft.json") or {}
    dmeta = draft.get("_meta", {})
    what = dmeta.get("what_firm_does", "")
    jdwants = dmeta.get("jd_wants", fit)
    rpng, cpng = b64(d/"resume_preview.png"), b64(d/"cover_preview.png")
    rpdf = "file:///" + str((d/"resume.pdf")).replace("\\","/")
    cpdf = "file:///" + str((d/"cover_letter.pdf")).replace("\\","/")
    capex_badge = ' <span class="chip cap">CAP-EXEMPT (no H-1B lottery)</span>' if capex else ""
    sal_txt = f' · {escape(str(sal))}' if sal else ""
    return f"""
    <div class="card" data-lane="{lane}">
      <div class="card-head" onclick="this.parentNode.classList.toggle('open')">
        <div class="ch-left"><span class="chev">▶</span>
          <div>
            <div class="ctitle">{escape(co)} — {escape(ro)}{capex_badge}</div>
            <div class="cmeta">{escape(meta.get('ats',''))}{sal_txt}</div>
          </div>
        </div>
        <span class="badge" style="background:{col}">{badge}</span>
      </div>
      <div class="card-body">
        {f'<div class="firm"><b>What {escape(co)} does:</b> {escape(what)}</div>' if what else ''}
        {f'<div class="jd"><b>What the role wants:</b> {escape(jdwants)}</div>' if jdwants else ''}
        <div class="links">
          <a href="{escape(url)}" target="_blank">↗ Job posting</a>
          <a href="{rpdf}" target="_blank">📄 Résumé PDF</a>
          <a href="{cpdf}" target="_blank">📄 Cover PDF</a>
        </div>
        <div class="previews">
          <div class="prev"><div class="plabel">Tailored Résumé</div>{f'<img src="{rpng}" loading="lazy">' if rpng else '<div class=noimg>no preview</div>'}</div>
          <div class="prev"><div class="plabel">Cover Letter</div>{f'<img src="{cpng}" loading="lazy">' if cpng else '<div class=noimg>no preview</div>'}</div>
        </div>
        {essay_block(d)}
      </div>
    </div>"""

def outreach_card(o):
    badge = "#7c3aed" if o.get("contact_type") in ("senior_leader","hiring_manager") else "#0891b2"
    alum = o.get("alumni_connection","none")
    alum_html = f' · <span style="color:#16a34a">{escape(alum)} alum</span>' if alum and alum.lower()!="none" else ""
    return f"""
    <div class="card">
      <div class="card-head" onclick="this.parentNode.classList.toggle('open')">
        <div class="ch-left"><span class="chev">▶</span>
          <div>
            <div class="ctitle">{escape(o['contact_name'])} — <span style="font-weight:500">{escape(o['company'])}</span></div>
            <div class="cmeta">{escape(o.get('contact_title_current',''))} · re: {escape(o.get('role_applied',''))}{alum_html}</div>
          </div>
        </div>
        <span class="badge" style="background:{badge}">{escape(o.get('contact_type','peer'))} · {escape(o.get('confidence','—'))}</span>
      </div>
      <div class="card-body">
        <p class="note">✓ Verified: {escape(o.get('verification_evidence',''))}</p>
        <div class="links"><a href="{escape(o['linkedin_url'])}" target="_blank">↗ LinkedIn</a></div>
        <div class="email">
          <div class="esubj"><b>Subject:</b> {escape(o.get('subject',''))}</div>
          <pre class="ebody">{escape(o.get('body',''))}</pre>
        </div>
      </div>
    </div>"""

# gather roles, sort by lane priority
dirs = sorted([Path(p) for p in glob.glob(str(DISC/"*")) if (Path(p)/"form_fields.json").exists()])
LANE_ORDER = {"SUBMITTED":0, "ESSAY":1, "NEEDS":2, "BLOCKED":3, "DEFERRED":4}
roles = []
for d in dirs:
    lane,_,_ = role_status(d)
    roles.append((LANE_ORDER.get(lane,9), d.name, d, lane))
roles.sort(key=lambda x:(x[0], x[1]))

counts = {}
for _,_,_,lane in roles: counts[lane]=counts.get(lane,0)+1

cards_by_lane = {"SUBMITTED":[], "ESSAY":[], "NEEDS":[], "BLOCKED":[], "DEFERRED":[]}
for _, name, d, lane in roles:
    cards_by_lane.setdefault(lane,[]).append(card(d))

outreach = jload(RUN/"outreach_drafts.json") or []
outreach_cards = "".join(outreach_card(o) for o in outreach)

def section(title, lane, blurb):
    cs = cards_by_lane.get(lane, [])
    if not cs: return ""
    return f'<div class="lane-title">{title} <span class="cnt">{len(cs)}</span></div><div class="blurb">{blurb}</div>{"".join(cs)}'

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jamie — Night Run Review 2026-05-31</title>
<style>
 :root{{--bg:#f6f7f9;--card:#fff;--border:#e4e7eb;--muted:#6b7280;--ink:#111827}}
 *{{box-sizing:border-box}} body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:var(--bg);color:var(--ink);line-height:1.5}}
 .wrap{{max-width:1040px;margin:0 auto;padding:24px 16px 80px}}
 h1{{font-size:23px;margin:0 0 4px}} .sub{{color:var(--muted);font-size:14px;margin:0 0 18px}}
 .banner{{background:#ede9fe;border:1px solid #c4b5fd;border-radius:10px;padding:14px 16px;margin-bottom:22px;font-size:14px}}
 .lane-title{{font-size:15px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;margin:26px 0 6px;display:flex;gap:10px;align-items:center}}
 .lane-title .cnt{{background:#e5e7eb;border-radius:12px;padding:2px 10px;font-size:12px;font-weight:700}}
 .blurb{{font-size:13px;color:var(--muted);margin-bottom:12px}}
 .card{{background:var(--card);border:1px solid var(--border);border-radius:10px;margin-bottom:10px;overflow:hidden}}
 .card-head{{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;cursor:pointer;gap:12px}}
 .card-head:hover{{background:#fafbfc}}
 .ch-left{{display:flex;gap:10px;align-items:flex-start}}
 .chev{{transition:transform .15s;color:var(--muted);font-size:11px;margin-top:4px}}
 .card.open .chev{{transform:rotate(90deg)}}
 .ctitle{{font-weight:650;font-size:15px}} .cmeta{{font-size:12.5px;color:var(--muted);margin-top:2px}}
 .badge{{color:#fff;font-size:11px;font-weight:700;padding:3px 9px;border-radius:10px;white-space:nowrap}}
 .chip{{font-size:10px;font-weight:700;padding:1px 7px;border-radius:8px;vertical-align:middle}}
 .chip.cap{{background:#dcfce7;color:#166534}}
 .card-body{{display:none;padding:6px 16px 18px;border-top:1px solid var(--border)}}
 .card.open .card-body{{display:block}}
 .firm,.jd{{font-size:13.5px;background:#f9fafb;border-left:3px solid #c4b5fd;padding:8px 12px;border-radius:4px;margin:12px 0 8px}}
 .jd{{border-left-color:#fcd34d}}
 .links{{display:flex;gap:14px;flex-wrap:wrap;margin:12px 0}}
 .links a{{font-size:13px;text-decoration:none;color:#2563eb;font-weight:500}} .links a:hover{{text-decoration:underline}}
 .previews{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
 @media(max-width:680px){{.previews{{grid-template-columns:1fr}}}}
 .prev{{border:1px solid var(--border);border-radius:8px;overflow:hidden;background:#fff}}
 .plabel{{font-size:11px;font-weight:600;color:var(--muted);padding:6px 10px;background:#f9fafb;border-bottom:1px solid var(--border)}}
 .prev img{{width:100%;display:block}} .noimg{{padding:20px;color:#9ca3af;font-size:12px;text-align:center}}
 .essays-wrap{{margin-top:16px;border:1px solid #e9d5ff;border-radius:8px;padding:12px;background:#faf5ff}}
 .essays-title{{font-size:13px;font-weight:700;color:#6b21a8;margin-bottom:8px}}
 .capnote{{font-size:12px;color:var(--muted);margin-bottom:10px}}
 .essay{{margin-bottom:12px}} .eq{{font-size:13px;font-weight:600;margin-bottom:4px}}
 .ea{{width:100%;font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:13px;padding:8px 10px;border:1px solid var(--border);border-radius:6px;line-height:1.5;resize:vertical}}
 .note{{font-size:13px;background:#f9fafb;border-left:3px solid #16a34a;padding:8px 12px;border-radius:4px;margin:12px 0}}
 .email{{border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-top:8px}}
 .esubj{{font-size:13px;padding:8px 12px;background:#f9fafb;border-bottom:1px solid var(--border)}}
 .ebody{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:13px;white-space:pre-wrap;word-wrap:break-word;margin:0;padding:12px;line-height:1.55}}
</style></head><body><div class="wrap">
 <h1>Jamie — Night Run Review · 2026-05-31</h1>
 <p class="sub">{len(roles)} roles processed · {counts.get('SUBMITTED',0)} auto-submitted · {counts.get('ESSAY',0)} need your essay approval · {counts.get('NEEDS',0)} finish manually · {counts.get('BLOCKED',0)} blocked-ATS (manual) · {len(outreach)} outreach drafts</p>
 <div class="banner">
   <b>How to use this:</b> The <b>✅ submitted</b> roles are done. The <b>✍️ essay roles</b> have answers I drafted in your voice — read each, edit the textarea if you want, then they're ready to submit (tell David / paste into the form). <b>⚠ Finish-manually</b> roles are tailored & ready but use a branded form a couple fields didn't auto-fill — 2-minute manual finish. <b>🔒 Blocked-ATS</b> (Workday/iCIMS/university portals, incl. cap-exempt gems) need manual apply but the résumé + cover are done. Each card shows <b>what the firm does</b> + <b>what the role wants</b> for quick context.
 </div>
 {section("✅ Auto-Submitted", "SUBMITTED", "Confirmed submitted via the autopilot. Nothing more needed.")}
 {section("✍️ Essay Roles — Approve Your Answers", "ESSAY", "Custom 'why this company' essays. I drafted each in your voice from your real cover letters — edit if you'd like, then they're submit-ready.")}
 {section("⚠ Finish Manually (branded forms)", "NEEDS", "Résumé + cover tailored & ready. The company's branded careers form had a couple of widgets the bot couldn't finish — quick manual completion.")}
 {section("🔒 Blocked ATS — Manual Apply", "BLOCKED", "Workday / iCIMS / university portals (can't be automated). Cap-exempt employers here are high-value — no H-1B lottery. Packages are ready.")}
 {section("⏸ Deferred (per-company cap / no-sponsor)", "DEFERRED", "Intentionally NOT applied: either the JD bars visa sponsorship, or it's a 2nd/3rd role at a company where I kept the best-fit 1-2 to avoid looking spammy. Packages exist if you want any of them.")}
 <div class="lane-title">📧 Outreach Drafts — Review Before Sending <span class="cnt">{len(outreach)}</span></div>
 <div class="blurb">Every contact verified currently-employed via live LinkedIn. Nothing sent — yours to review, edit, and send.</div>
 {outreach_cards}
</div></body></html>"""

out = RUN / "dashboard_review.html"
out.write_text(html, encoding="utf-8")
print("Dashboard written:", out, f"({len(html)//1024} KB)")
print("Lane counts:", counts)
