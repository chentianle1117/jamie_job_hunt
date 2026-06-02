#!/usr/bin/env python3
"""Add a `meta` block to tonight's flat form_fields.json so the master dashboard ingests them."""
import json, os

BASE = os.path.join(os.path.dirname(__file__), "discovered")
state = json.load(open(os.path.join(os.path.dirname(__file__), "state.json"), encoding="utf-8"))
by_slug = {a["slug"]: a for a in state["applications"]}

for slug in sorted(os.listdir(BASE)):
    fp = os.path.join(BASE, slug, "form_fields.json")
    if not os.path.exists(fp):
        continue
    ff = json.load(open(fp, encoding="utf-8"))
    a = by_slug.get(slug, {})
    ff["meta"] = {
        "company": ff.get("company", a.get("company", "")),
        "role": ff.get("role", a.get("title", "")),
        "ats": ff.get("ats", a.get("ats", "")),
        "url": ff.get("role_url", a.get("url", "")),
        "date": "2026-06-02",
        "id": slug,
        "bucket": a.get("ats", ""),
        "min_years": str(a.get("yoe_required", "")),
        "why_fit": "; ".join(a.get("flags", []))[:200],
        "lane": a.get("lane", "PACKAGE_READY"),
        "fit_pct": a.get("fit_pct"),
        "cap_exempt": True,
        "h1b_signal": "cap-exempt"
    }
    json.dump(ff, open(fp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("[meta added] " + slug)
