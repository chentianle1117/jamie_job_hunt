#!/usr/bin/env python3
"""Batch-submit tonight's auto-submittable roles via the right ATS handler over CDP.
Reads each role's form_fields.json meta.ats. Greenhouse/embed -> submit_llm_generic.
Ashby -> submit_ashby_generic. Lever handled by ashby handler's generic path if present, else skipped.
Honors DRY env. Skips roles flagged no-sponsor or already SUBMITTED (idempotent re-run).
Usage: python submit_batch.py [only_substring]   (optional filter)
Env: DRY=1, CDP_PORT=9222
"""
import json, os, sys, subprocess
from pathlib import Path

RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-30_night")
DISC = RUN/"discovered"
LIB = Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
GH = str(LIB/"submit_llm_generic.py")
ASHBY = str(LIB/"submit_ashby_generic.py")

# roles to skip:
#  - explicit no-sponsor
#  - per-company sound-judgment cap (David 2026-05-31): keep the 1-2 BEST-fit per company,
#    defer weaker duplicates to minimize spammy-looking volume at one employer.
SKIP_IDS = {
    "affirm_workplace_manager",            # JD: "No visa sponsorship available"
    # --- per-company cap: defer the weaker duplicate (keep the stronger sibling) ---
    "anthropic_implementation_specialist", # keep Program Ops Mgr (Impl Spec = deep technical stretch)
    "figma_onboarding_manager_customer",   # keep Customer Enablement Mgr (same lane, better match)
    "chime_program_manager_dispute",       # keep Performance Effectiveness (closer to OD)
    "robinhood_people_systems_manager",    # keep Manager of L&D (Systems = 7+yr Workday stretch)
    "notion_people_partner_epd",           # keep CS Enablement PM (EPD = 10+yr stretch)
    "datadog_inclusion_program_manager",   # keep PBP + Solutions Coord (2 already strong at Datadog)
}

only = sys.argv[1] if len(sys.argv) > 1 else None
env = dict(os.environ); env.setdefault("CDP_PORT", "9222")

roles = sorted([d for d in DISC.iterdir() if d.is_dir() and (d/"form_fields.json").exists()])
results = []
for d in roles:
    ff = json.load(open(d/"form_fields.json", encoding="utf-8"))
    rid = ff["meta"]["id"]; ats = (ff["meta"].get("ats") or "").lower()
    if only and only not in rid: continue
    if rid in SKIP_IDS:
        print(f"SKIP (no-sponsor): {rid}", flush=True); results.append((rid, "skip_nosponsor")); continue
    # idempotent: skip if already successfully submitted
    sj = d/"SUBMITTED.json"
    if sj.exists():
        try:
            j = json.load(open(sj, encoding="utf-8"))
            if j.get("success"):
                print(f"SKIP (already submitted): {rid}", flush=True); results.append((rid, "already_done")); continue
        except: pass
    if not (d/"resume.pdf").exists():
        print(f"SKIP (no resume.pdf): {rid}", flush=True); results.append((rid, "no_pdf")); continue

    if ats == "greenhouse":
        script = GH
    elif ats == "ashby":
        script = ASHBY
    elif ats == "lever":
        # lever forms are simple; ashby handler has a generic fallback - try it
        script = ASHBY
    else:
        print(f"SKIP (blocked ATS {ats}): {rid}", flush=True); results.append((rid, f"blocked_{ats}")); continue

    print(f"\n###### {rid}  [{ats}] ######", flush=True)
    try:
        r = subprocess.run([sys.executable, script, str(d)], env=env, timeout=300,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        # surface key lines
        for line in out.splitlines():
            if any(k in line for k in ["Success=","SUBMITTED","unanswered","CDP","questions to answer","[OK]","[??]","?","ERR","err","Nav:"]):
                print("  "+line, flush=True)
        # read result
        status = "unknown"
        if sj.exists():
            try:
                j = json.load(open(sj, encoding="utf-8"))
                status = "SUBMITTED" if j.get("success") else f"incomplete({len(j.get('unanswered_required',[]))})"
            except: pass
        results.append((rid, status))
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {rid}", flush=True); results.append((rid, "timeout"))
    except Exception as e:
        print(f"  EXC: {e}", flush=True); results.append((rid, f"exc:{e}"))

print("\n=== BATCH SUMMARY ===", flush=True)
for rid, st in results: print(f"  {st:22} {rid}", flush=True)
done = sum(1 for _,s in results if s=="SUBMITTED")
print(f"\nSUBMITTED {done} / attempted {len([r for r in results if r[1] not in ('skip_nosponsor','already_done','no_pdf') and not r[1].startswith('blocked')])}", flush=True)
