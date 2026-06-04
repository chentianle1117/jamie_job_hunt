#!/usr/bin/env python3
"""Normalize tonight's flat form_fields.json into the nested schema the submitters expect
(meta.url, personal.*, links.linkedin), for the 3 auto-submit packages. Also promote
essay_answers_draft.json -> essay_answers.json (approved) so the submitters can answer questions.
Run after David approved all 3 submissions."""
import json, os

BASE = os.path.join(os.path.dirname(__file__), "discovered")
AUTO = ["openai_customer_education_pm", "openai_pm_human_data", "databricks_customer_enablement"]

for slug in AUTO:
    d = os.path.join(BASE, slug)
    ffp = os.path.join(d, "form_fields.json")
    ff = json.load(open(ffp, encoding="utf-8"))
    name = ff.get("name", "Jamie (Yi-Chieh) Cheng")
    # split name -> first/last (Ashby/Greenhouse want first+last)
    first, last = "Yi-Chieh", "Cheng"
    ff["meta"] = {
        "company": ff.get("company", ""),
        "role": ff.get("role", ""),
        "url": ff.get("role_url", ""),
        "ats": ff.get("ats", ""),
        "date": "2026-06-04",
        "id": slug,
    }
    ff["personal"] = {
        "first_name": first,
        "last_name": last,
        "email": ff.get("email", "jamiecheng0103@gmail.com"),
        "phone": ff.get("phone", "213-700-3831"),
        "location": ff.get("location", "Portland, OR"),
        "country": "United States",
    }
    ff["links"] = {"linkedin": ff.get("linkedin", "http://www.linkedin.com/in/jamieyccheng")}
    json.dump(ff, open(ffp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    # promote essay drafts to approved (David approved these submissions)
    draftp = os.path.join(d, "essay_answers_draft.json")
    apprp = os.path.join(d, "essay_answers.json")
    if os.path.exists(draftp) and not os.path.exists(apprp):
        draft = json.load(open(draftp, encoding="utf-8"))
        # draft may be {"answers":[{question,answer}]} or {question:answer}; normalize to {question:answer}
        approved = {}
        if isinstance(draft, dict) and "answers" in draft:
            for a in draft["answers"]:
                q = a.get("question", "").strip()
                if q:
                    approved[q] = a.get("answer", "")
        elif isinstance(draft, dict):
            for k, v in draft.items():
                if k != "meta" and isinstance(v, str):
                    approved[k] = v
        json.dump(approved, open(apprp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"[{slug}] normalized form_fields + promoted {len(approved)} essays")
    else:
        print(f"[{slug}] normalized form_fields (essays: {'exists' if os.path.exists(apprp) else 'none'})")
