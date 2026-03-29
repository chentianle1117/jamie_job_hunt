#!/usr/bin/env python3
"""
Greenhouse + Lever API Job Fetcher for Jamie's Oracle Pipeline.

Queries public (no-auth) ATS APIs for all mapped companies and filters
for People/HR/OD/L&D roles. Outputs a JSON file that the main pipeline
can read as a pre-verified discovery source.

Usage:
    python fetch_ats_jobs.py                      # default: output to pipeline/ats_jobs.json
    python fetch_ats_jobs.py --output results.json # custom output path
    python fetch_ats_jobs.py --test                # dry-run: print stats only

APIs used (both are PUBLIC, no auth required):
    Greenhouse: GET https://api.greenhouse.io/v1/boards/{slug}/jobs?content=true
    Lever:      GET https://api.lever.co/v0/postings/{slug}?mode=json

Requires: requests (pip install requests)
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Run: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
ATS_MAPPING = SCRIPT_DIR.parent / "ats_mapping.json"
DEFAULT_OUTPUT = Path("C:/Windows/Temp/ats_jobs.json")

# Keywords to match People/HR/OD/L&D roles (case-insensitive)
# These must appear in the job TITLE — broad terms like "people" are combined
# with role-type words to avoid false positives (e.g., "People Partner" yes, "ML Engineer" no)
INCLUDE_KEYWORDS = [
    r"\bpeople\s+partner\b", r"\bpeople\s+program\b", r"\bpeople\s+ops\b",
    r"\bpeople\s+operations\b", r"\bpeople\s+science\b", r"\bpeople\s+analytics\b",
    r"\bpeople\s+experience\b", r"\bpeople\s+coordinator\b", r"\bpeople\s+specialist\b",
    r"\bpeople\s+manager\b", r"\bpeople\s+associate\b", r"\bpeople\s+support\b",
    r"\btalent\s+dev", r"\btalent\s+program\b", r"\btalent\s+manag",
    r"\btalent\s+operations\b", r"\btalent\s+partner\b", r"\btalent\s+acquisition\b",
    r"\btalent\s+engagement\b", r"\btalent\s+specialist\b", r"\btalent\s+coordinator\b",
    r"\bhr\b", r"\bhuman\s+resources?\b", r"\bhrbp\b",
    r"\borg(anizational)?\s+dev(elopment)?\b",
    r"\bl&d\b", r"\blearning\s+(and\s+)?dev(elopment)?\b", r"\blearning\s+program\b",
    r"\blearning\s+operations?\b", r"\blearning\s+specialist\b", r"\blearning\s+coordinator\b",
    r"\btraining\s+manag", r"\btraining\s+specialist\b", r"\btraining\s+coordinator\b",
    r"\bemployee\s+experience\b", r"\bemployee\s+engagement\b",
    r"\bculture\s+(and\s+)?engagement\b", r"\bculture\s+specialist\b",
    r"\bchange\s+management\b", r"\bocm\b",
    r"\bdei\b", r"\bdiversity\b.*\binclusion\b",
    r"\bworkforce\s+dev", r"\bworkforce\s+planning\b",
]

# Exclude senior/director/VP roles
EXCLUDE_KEYWORDS = [
    r"\bsenior\s+director\b", r"\bvice\s+president\b", r"\bvp\b",
    r"\bchief\b", r"\bprincipal\b", r"\bstaff\b",
    r"\bdirector\b",  # catch "Director of People" etc.
]

# Allow these even if they contain an exclude keyword
ALLOW_OVERRIDE = [
    r"\bassociate\s+director\b",  # sometimes junior-ish at small cos
    r"\bsenior\s+associate\b",     # consulting = okay
]

INCLUDE_RE = re.compile("|".join(INCLUDE_KEYWORDS), re.IGNORECASE)
EXCLUDE_RE = re.compile("|".join(EXCLUDE_KEYWORDS), re.IGNORECASE)
ALLOW_RE = re.compile("|".join(ALLOW_OVERRIDE), re.IGNORECASE)

# Rate-limit: be nice to free APIs
REQUEST_DELAY = 0.3  # seconds between requests


def matches_role(title: str) -> bool:
    """Return True if the job title looks like a People/HR/OD/L&D role at an appropriate level."""
    if not INCLUDE_RE.search(title):
        return False
    if EXCLUDE_RE.search(title) and not ALLOW_RE.search(title):
        return False
    return True


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------

def fetch_greenhouse(slug: str, company_name: str) -> list[dict]:
    """Fetch jobs from Greenhouse Job Board API and filter for relevant roles."""
    url = f"https://api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    results = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        if not matches_role(title):
            continue

        location = job.get("location", {}).get("name", "Unknown")
        job_url = job.get("absolute_url", "")
        updated = job.get("updated_at", "")
        content_html = job.get("content", "")
        # Strip HTML tags for plain text
        content_text = re.sub(r"<[^>]+>", " ", content_html)
        content_text = re.sub(r"\s+", " ", content_text).strip()

        results.append({
            "source": "greenhouse_api",
            "company": company_name,
            "title": title,
            "location": location,
            "url": job_url,
            "updated_at": updated,
            "jd_snippet": content_text[:500],
            "ats": "greenhouse",
            "slug": slug,
        })

    return results


# ---------------------------------------------------------------------------
# Lever
# ---------------------------------------------------------------------------

def fetch_lever(slug: str, company_name: str) -> list[dict]:
    """Fetch jobs from Lever Postings API and filter for relevant roles."""
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    results = []
    for posting in data:
        title = posting.get("text", "")
        if not matches_role(title):
            continue

        cats = posting.get("categories", {})
        location = cats.get("location", "Unknown")
        team = cats.get("team", "")
        commitment = cats.get("commitment", "")
        job_url = posting.get("hostedUrl", "")
        created = posting.get("createdAt", 0)
        # Lever timestamps are milliseconds
        if created:
            created_dt = datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
        else:
            created_dt = ""

        desc_plain = posting.get("descriptionPlain", "")

        results.append({
            "source": "lever_api",
            "company": company_name,
            "title": title,
            "location": location,
            "team": team,
            "commitment": commitment,
            "url": job_url,
            "created_at": created_dt,
            "jd_snippet": desc_plain[:500],
            "ats": "lever",
            "slug": slug,
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch ATS jobs for Jamie's pipeline")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help="Output JSON path")
    parser.add_argument("--test", action="store_true",
                        help="Dry run: print stats, don't write file")
    args = parser.parse_args()

    if not ATS_MAPPING.exists():
        print(f"ERROR: ATS mapping not found at {ATS_MAPPING}")
        sys.exit(1)

    with open(ATS_MAPPING) as f:
        mapping = json.load(f)

    all_jobs = []
    stats = {"greenhouse_queried": 0, "lever_queried": 0,
             "greenhouse_hits": 0, "lever_hits": 0, "errors": []}

    # Greenhouse
    print("=== Greenhouse API ===")
    for key, info in mapping.get("greenhouse", {}).items():
        slug = info["slug"]
        name = info["name"]
        print(f"  [{slug}] {name}...", end=" ", flush=True)
        jobs = fetch_greenhouse(slug, name)
        stats["greenhouse_queried"] += 1
        stats["greenhouse_hits"] += len(jobs)
        all_jobs.extend(jobs)
        print(f"{len(jobs)} matches")
        time.sleep(REQUEST_DELAY)

    # Lever
    print("\n=== Lever API ===")
    for key, info in mapping.get("lever", {}).items():
        slug = info["slug"]
        name = info["name"]
        print(f"  [{slug}] {name}...", end=" ", flush=True)
        jobs = fetch_lever(slug, name)
        stats["lever_queried"] += 1
        stats["lever_hits"] += len(jobs)
        all_jobs.extend(jobs)
        print(f"{len(jobs)} matches")
        time.sleep(REQUEST_DELAY)

    # Summary
    total = len(all_jobs)
    print(f"\n=== SUMMARY ===")
    print(f"  Greenhouse: {stats['greenhouse_queried']} companies queried, {stats['greenhouse_hits']} People/HR roles found")
    print(f"  Lever:      {stats['lever_queried']} companies queried, {stats['lever_hits']} People/HR roles found")
    print(f"  TOTAL:      {total} relevant jobs across all ATS APIs")

    if args.test:
        print("\n[TEST MODE] No file written.")
        if all_jobs:
            print("\nSample matches:")
            for j in all_jobs[:10]:
                print(f"  - {j['title']} @ {j['company']} ({j['location']})")
        return

    # Write output
    output_path = Path(args.output)
    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "jobs": all_jobs,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to: {output_path}")


if __name__ == "__main__":
    main()
