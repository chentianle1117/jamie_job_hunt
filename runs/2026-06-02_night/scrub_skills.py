#!/usr/bin/env python3
"""Strip tools NOT in Jamie's verified corpus from package skills lines. Canva kept (low-risk)."""
import json, re, os

BASE = os.path.join(os.path.dirname(__file__), "discovered")
UNVERIFIED = ["Constant Contact", "WordPress", "Airtable", "Qualtrics", "Salesforce", "Tableau", "Power BI"]

for r in sorted(os.listdir(BASE)):
    fp = os.path.join(BASE, r, "resume.json")
    if not os.path.exists(fp):
        continue
    d = json.load(open(fp, encoding="utf-8"))
    skills = d.get("skills", [])
    newskills = []
    changed = False
    for line in skills:
        orig = line
        for t in UNVERIFIED:
            line = re.sub(r"\s*\(" + re.escape(t) + r"\)", "", line)
            line = re.sub(r",\s*" + re.escape(t) + r"\b", "", line)
            line = re.sub(r"\b" + re.escape(t) + r",\s*", "", line)
            line = re.sub(r"\s*[·]\s*" + re.escape(t) + r"\b", "", line)
            line = re.sub(r"\b" + re.escape(t) + r"\s*[·]\s*", "", line)
            line = re.sub(r"\b" + re.escape(t) + r"\b", "", line)
        line = re.sub(r"\(\s*\)", "", line)
        line = re.sub(r"\(\s*,\s*", "(", line)
        line = re.sub(r"\s*,\s*\)", ")", line)
        line = re.sub(r"[·]\s*[·]", "·", line)
        line = re.sub(r"\s{2,}", " ", line).strip()
        line = line.rstrip("·").strip()
        if line != orig:
            changed = True
        newskills.append(line)
    if changed:
        d["skills"] = newskills
        json.dump(d, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print("[SCRUBBED] " + r)
        print("    " + newskills[0][:140])
    else:
        print("[clean]    " + r)
