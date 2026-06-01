import json, os, sys, subprocess
from pathlib import Path
RUN=Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-31_round2")
DISC=RUN/"discovered"; LIB=Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
GH=str(LIB/"submit_llm_generic.py"); ASHBY=str(LIB/"submit_ashby_generic.py")
env=dict(os.environ); env["CDP_PORT"]=os.environ.get("CDP_PORT","9333")
# the 6 unrun + 5 near-miss
TARGETS=["cursor_recruiting_coordinator","discord_recruiting_data_analyst","duolingo_manager_strategy_and",
 "duolingo_recruiter_ii_nyc","duolingo_recruiter_ii_pittsburgh","samsara_enablement_business_partner",
 "samsara_recruiting_coordinator","cohere_recruitment_coordinator","crusoe_workplace_coordinator",
 "persona_operations_analyst","sierra_recruiting_coordinator_contract","unit_support_operations_specialist"]
results=[]
for name in TARGETS:
    d=DISC/name
    if not (d/"form_fields.json").exists(): print(f"SKIP missing: {name}",flush=True); continue
    sj=d/"SUBMITTED.json"
    if sj.exists() and json.load(open(sj,encoding="utf-8")).get("success"): print(f"SKIP done: {name}",flush=True); continue
    ats=(json.load(open(d/"form_fields.json",encoding="utf-8"))["meta"].get("ats") or "").lower()
    script=GH if ats=="greenhouse" else ASHBY
    print(f"\n###### {name} [{ats}] ######",flush=True)
    try:
        r=subprocess.run([sys.executable,script,str(d)],env=env,timeout=340,capture_output=True,text=True,encoding="utf-8",errors="replace")
        for ln in (r.stdout or "").splitlines():
            if any(k in ln for k in ["Success=","SUBMITTED","unanswered","Nav:","essay","REVIEW"]): print("  "+ln,flush=True)
        st="?"
        if sj.exists():
            j=json.load(open(sj,encoding="utf-8")); st="SUBMITTED" if j.get("success") else f"inc({len(j.get('unanswered_required',[]))})"
        results.append((name,st))
    except subprocess.TimeoutExpired: results.append((name,"timeout")); print("  TIMEOUT",flush=True)
    except Exception as e: results.append((name,f"err")); print(f"  ERR {e}",flush=True)
print("\n=== RETRY SUMMARY ===",flush=True)
for n,s in results: print(f"  {s:12} {n}",flush=True)
print("SUBMITTED",sum(1 for _,s in results if s=="SUBMITTED"),"/",len(results),flush=True)
