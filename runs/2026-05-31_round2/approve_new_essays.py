import json, os
from pathlib import Path
D = Path(r"C:\Users\chent\Agentic_Workflows_2026\oracle-job-search\runs\2026-05-31_round2\discovered")

AI_ANSWER = ("AI has become part of how I work day-to-day, not a side tool. I use it to move faster from messy "
"input to a clear decision—synthesizing stakeholder feedback, drafting and pressure-testing communications, "
"and spotting patterns in data I'd otherwise comb through by hand. What's changed most is my starting point: I "
"now ask what a well-designed AI workflow could take off my plate before I default to doing it manually. I've "
"even been building a RAG-style system for my own job search with a friend, where the AI has access to my "
"background and preferences so it can evaluate fit for me specifically—which made me realize how much the "
"same personalization principle scales to real work. I still treat the output as a draft to verify, not gospel; "
"the judgment stays mine.")

ATS_ANSWER = ("Greenhouse is the ATS I've used most extensively—I have hands-on administrative experience "
"posting jobs, scheduling interviews, emailing candidates, and managing the talent pipeline and data within it "
"(I've also used Rippling, ADP, and SAP at the user level). To calculate a metric like time-to-fill, I'd define "
"it cleanly first: days from when a requisition opens to when an offer is accepted, measured per role and then "
"aggregated using the median, not just the mean, so a few outliers don't distort it. I'd pull the stage "
"timestamps Greenhouse logs, segment by team and source, and watch the trend over time rather than a single "
"snapshot—because the point isn't the number, it's spotting where the funnel actually slows down.")

WHOLE_SELF = ("Bringing my whole self to work means leading with curiosity and genuine care for the people behind "
"the process. I'm a 97% extrovert who loves understanding what makes teams tick, and my background is "
"cross-cultural—I've worked across the US, Taiwan, and with a Danish company, including an office of 22 "
"nationalities—so I'm at my best building inclusion that's real, not surface-level. I also bring an "
"analytical, evidence-first mindset from my Organizational Psychology training: I ask the right questions, dig "
"for root causes, and care as much about the human side as the outcome.")

SAMSARA_OTHER = "LinkedIn"

PLANS = {
 "duolingo_manager_strategy_and": {"How has AI changed the way you approach your work?": AI_ANSWER},
 "duolingo_recruiter_ii_nyc": {"How has AI changed the way you approach your work?": AI_ANSWER},
 "duolingo_recruiter_ii_pittsburgh": {"How has AI changed the way you approach your work?": AI_ANSWER},
 "discord_recruiting_data_analyst": {"Name the ATS you've used most extensively and describe in 2-3 sentences how you would calculate a recruiting metric": ATS_ANSWER},
 "samsara_enablement_business_partner": {"At Samsara, we encourage employees to bring their whole selves to work": WHOLE_SELF, "If you selected 'Other' for where you learned about Samsara, please share additional details": SAMSARA_OTHER},
 "samsara_recruiting_coordinator": {"At Samsara, we encourage employees to bring their whole selves to work": WHOLE_SELF, "If you selected 'Other' for where you learned about Samsara, please share additional details": SAMSARA_OTHER},
}
for rid, ans in PLANS.items():
    p = D / rid / "essay_answers.json"
    existing = {}
    if p.exists():
        try: existing = json.load(open(p, encoding="utf-8"))
        except: pass
    existing.update(ans)
    json.dump(existing, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("approved:", rid, "->", list(ans.keys()))
print("done")
