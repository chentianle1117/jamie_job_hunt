import json, os, sys, subprocess
from pathlib import Path
RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-30_night")
DISC = RUN/"discovered"; LIB = Path(r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
GH=str(LIB/"submit_llm_generic.py"); ASHBY=str(LIB/"submit_ashby_generic.py")
env=dict(os.environ); env["CDP_PORT"]=os.environ.get("CDP_PORT","9333")
roles=[d for d in sorted(DISC.iterdir()) if d.is_dir() and (d/"essay_answers.json").exists()]
results=[]
for d in roles:
    ff=json.load(open(d/"form_fields.json",encoding="utf-8")); ats=(ff["meta"].get("ats") or "").lower()
    sj=d/"SUBMITTED.json"
    if sj.exists() and json.load(open(sj,encoding="utf-8")).get("success"):
        print(f"SKIP done: {d.name}"); continue
    script = GH if ats=="greenhouse" else ASHBY
    print(f"\n###### {d.name} [{ats}] ######", flush=True)
    try:
        r=subprocess.run([sys.executable,script,str(d)],env=env,timeout=320,capture_output=True,text=True,encoding="utf-8",errors="replace")
        for line in (r.stdout or "").splitlines():
            if any(k in line for k in ["Success=","SUBMITTED","essay","REVIEW","unanswered","Nav:","[OK]","[??]"]): print("  "+line,flush=True)
        st="?"
        if sj.exists():
            j=json.load(open(sj,encoding="utf-8")); st="SUBMITTED" if j.get("success") else f"incomplete({len(j.get('unanswered_required',[]))})"
        results.append((d.name,st))
    except subprocess.TimeoutExpired: results.append((d.name,"timeout")); print("  TIMEOUT",flush=True)
print("\n=== ESSAY SUBMIT SUMMARY ===")
for n,s in results: print(f"  {s:18} {n}")
print("SUBMITTED",sum(1 for _,s in results if s=="SUBMITTED"),"/",len(results))
