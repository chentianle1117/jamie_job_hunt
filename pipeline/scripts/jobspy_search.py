#!/usr/bin/env python3
"""
JobSpy Pre-Search for Jamie's Oracle Pipeline.

Uses the python-jobspy library to scrape LinkedIn, Indeed, and Glassdoor
for People/HR/OD/L&D roles. Outputs CSV + JSON for the main pipeline.

Indeed has NO rate limiting (best source).
LinkedIn caps at ~page 10 per IP (~100 results per query).
Glassdoor works but is slower.

Usage:
    python jobspy_search.py                        # default search
    python jobspy_search.py --location "Amsterdam"  # EU search
    python jobspy_search.py --test                  # dry-run

Requires: python-jobspy (pip install python-jobspy)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from jobspy import scrape_jobs
except ImportError:
    print("ERROR: 'python-jobspy' package required. Run: pip install python-jobspy")
    print("       Also requires: pip install requests beautifulsoup4")
    sys.exit(1)

DEFAULT_OUTPUT_JSON = Path("C:/Windows/Temp/jobspy_results.json")
DEFAULT_OUTPUT_CSV = Path("C:/Windows/Temp/jobspy_results.csv")

# Search configurations for Jamie's target roles
SEARCH_CONFIGS = [
    {
        "name": "People Program Manager",
        "term": '"people program manager" OR "HR program manager" OR "talent program manager"',
        "location": "Portland, OR",
        "distance": 50,
        "results": 30,
    },
    {
        "name": "People Program Manager (Remote)",
        "term": '"people program manager" OR "HR program manager"',
        "location": "United States",
        "is_remote": True,
        "results": 30,
    },
    {
        "name": "OD / Employee Experience",
        "term": '"organizational development" OR "employee experience" OR "engagement specialist"',
        "location": "Portland, OR",
        "distance": 50,
        "results": 20,
    },
    {
        "name": "L&D Operations",
        "term": '"learning and development" OR "L&D" OR "training manager" OR "learning operations"',
        "location": "Portland, OR",
        "distance": 50,
        "results": 20,
    },
    {
        "name": "Talent Development Consulting",
        "term": '"talent development consultant" OR "people advisory" OR "OD consultant" OR "HR consultant"',
        "location": "United States",
        "is_remote": True,
        "results": 20,
    },
    {
        "name": "Junior HRBP",
        "term": '"associate HRBP" OR "HRBP assistant" OR "junior people partner" OR "HR associate"',
        "location": "Portland, OR",
        "distance": 50,
        "results": 20,
    },
]

# Netherlands-specific searches
NL_SEARCH_CONFIGS = [
    {
        "name": "People/HR Netherlands",
        "term": '"people" OR "HR" OR "talent" OR "organizational development"',
        "location": "Netherlands",
        "results": 30,
        "country": "nl",
    },
    {
        "name": "People Program NL",
        "term": '"people program" OR "HR program" OR "employee experience"',
        "location": "Amsterdam",
        "results": 20,
        "country": "nl",
    },
]


def run_search(config: dict, sites: list[str] = None) -> list[dict]:
    """Run a single JobSpy search and return results as dicts."""
    if sites is None:
        sites = ["indeed", "linkedin"]  # Indeed = no rate limit, LinkedIn = capped

    kwargs = {
        "site_name": sites,
        "search_term": config["term"],
        "location": config["location"],
        "results_wanted": config.get("results", 20),
        "hours_old": 72,  # last 3 days
    }

    if config.get("is_remote"):
        kwargs["is_remote"] = True
    if config.get("distance"):
        kwargs["distance"] = config["distance"]
    if config.get("country"):
        kwargs["country_indeed"] = config["country"]

    try:
        df = scrape_jobs(**kwargs)
        if df is None or df.empty:
            return []
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"  ERROR: {e}")
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JobSpy search for Jamie's pipeline")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--csv", type=str, default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--location", type=str, default=None,
                        help="Override location for all searches")
    parser.add_argument("--include-nl", action="store_true",
                        help="Also run Netherlands-specific searches")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    all_results = []
    configs = SEARCH_CONFIGS.copy()
    if args.include_nl:
        configs.extend(NL_SEARCH_CONFIGS)

    for config in configs:
        if args.location:
            config["location"] = args.location

        name = config["name"]
        print(f"Searching: {name}...", end=" ", flush=True)
        results = run_search(config)
        print(f"{len(results)} results")
        for r in results:
            r["search_category"] = name
        all_results.extend(results)

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = str(r.get("job_url", r.get("link", "")))
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    print(f"\n=== SUMMARY ===")
    print(f"  Total results: {len(all_results)}")
    print(f"  After dedup:   {len(unique_results)}")

    if args.test:
        print("\n[TEST MODE] No files written.")
        for r in unique_results[:10]:
            title = r.get("title", "Unknown")
            company = r.get("company_name", r.get("company", "Unknown"))
            loc = r.get("location", "Unknown")
            print(f"  - {title} @ {company} ({loc})")
        return

    # Write JSON
    output_data = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(unique_results),
        "jobs": unique_results,
    }
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
    print(f"JSON written to: {output_path}")

    # Write CSV
    try:
        import pandas as pd
        df = pd.DataFrame(unique_results)
        csv_path = Path(args.csv)
        df.to_csv(csv_path, index=False)
        print(f"CSV written to: {csv_path}")
    except ImportError:
        print("pandas not installed — CSV export skipped")


if __name__ == "__main__":
    main()
