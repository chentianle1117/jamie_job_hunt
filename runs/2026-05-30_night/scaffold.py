#!/usr/bin/env python3
"""Scaffold role dirs + form_fields.json for every candidate. Idempotent."""
import json, re
from pathlib import Path

RUN = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-30_night")
cands = json.load(open(RUN/"candidates_raw.json", encoding="utf-8"))

PERSONAL = {
    "first_name":"Yi-Chieh","last_name":"Cheng","email":"jamiecheng0103@gmail.com",
    "phone":"+1-213-700-3831","country":"United States","location":"Portland, OR"
}
LINKS = {"linkedin":"https://www.linkedin.com/in/jamieyccheng/"}
WORKAUTH = {"currently_authorized_to_work_in_us":"Yes","sponsorship_required":"Yes",
            "sponsorship_notes":"Will require H-1B sponsorship. Currently on valid work authorization."}
DEMO = {"gender":"Woman","race_ethnicity":"Asian","hispanic_latino":"No",
        "veteran":"I am not a protected veteran","disability":"No, I do not have a disability"}

def slugify(company, title):
    s = (company.split()[0] + "_" + "_".join(title.lower().replace("&","").replace(",","").split()[:3]))
    return re.sub(r'[^a-z0-9_]+','', s.lower())[:40]

def ats_label(a):
    return {"greenhouse":"Greenhouse","ashby":"Ashby","lever":"Lever","workday":"Workday",
            "icims":"iCIMS","other":"Other"}.get(a, a)

made = []
for bucket, items in cands.items():
    for c in items:
        sid = slugify(c["company"], c["title"])
        d = RUN/"discovered"/sid
        d.mkdir(parents=True, exist_ok=True)
        ff = {
            "meta":{"company":c["company"],"role":c["title"],"ats":ats_label(c["ats"]),
                    "url":c["apply_url"],"date":"2026-05-30","id":sid,
                    "bucket":bucket,"h1b_signal":c.get("h1b_signal"),
                    "cap_exempt":c.get("cap_exempt", False),"why_fit":c.get("why_fit"),
                    "level":c.get("level"),"salary":c.get("salary")},
            "personal":PERSONAL,"links":LINKS,"work_authorization":WORKAUTH,
            "demographics":DEMO,
            "role_specific":{"years_experience":"3 years","currently_us_based":"Yes","open_to_relocation":"Yes"},
            "salary":{"expected_range":"Open / within posted band","notes":"Flexible, open to discussion"},
            "documents":{"resume":"resume.pdf","cover_letter":"cover_letter.pdf"}
        }
        json.dump(ff, open(d/"form_fields.json","w",encoding="utf-8"), indent=2, ensure_ascii=False)
        made.append((bucket, sid, c["company"], c["title"], c["apply_url"]))

print(f"Scaffolded {len(made)} role dirs")
for b, sid, co, t, u in made:
    print(f"  [{b:18}] {sid:38} {co} — {t[:40]}")
