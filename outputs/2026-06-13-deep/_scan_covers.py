import sys, os
sys.path.insert(0, r"C:\Users\chent\Agentic_Workflows_2026\jamie-autopilot\lib")
from cover_truth_gate import scan_cover

base = r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\outputs\2026-06-13-deep\applications"
slugs = ["sierra_people_ops", "chime_senior_people_partner", "vercel_senior_hrbp_epd"]
allclean = True
for slug in slugs:
    p = os.path.join(base, slug, "cover_letter.md")
    txt = open(p, encoding="utf-8").read()
    flags = scan_cover(txt)
    print(f"=== {slug}: {len(flags)} flag(s) ===")
    if flags:
        allclean = False
    for f in flags:
        print("   [" + f["type"] + "] " + f["match"])
        print("       ctx:", f["context"][:180])
print("\nALL_CLEAN:" , allclean)
