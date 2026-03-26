# 🤝 Networking Outreach Protocol & Templates

> **Purpose:** For each job pick, identify 2-3 real networking contacts and draft
> personalized outreach messages in Jamie's voice. Messages should feel genuine,
> reference something specific about the contact's work, and lead to a natural
> conversation — NOT a transactional referral ask.

---

## Jamie's Outreach Style (Ground Truth)

### Key Characteristics
- **Warm and genuine** — not corporate or formulaic
- **References something specific** about the contact's work/role
- **Positions herself as earlier-career** seeking to learn — not as an equal asking for favors
- **Short** — 3-4 sentences max for LinkedIn connection request
- **Ends with gratitude** and openness
- **Emoji usage:** Minimal, occasional (✌️ 😊), sign-off sometimes playful
- **Bilingual sign-off option:** 可爱鸟鸟 🐣 (for Chinese-speaking contacts)

### What Jamie DOES NOT do
- Ask directly for a referral in the first message
- Use generic "I'd love to pick your brain" language
- Send identical messages to multiple people
- Lead with her own resume/achievements
- Sound desperate or overly formal

### The Jamie Formula
```
1. Greeting + how she found them (specific)
2. Something genuine about THEIR work she noticed (1 sentence)
3. Express interest in learning / connecting (soft ask)
4. Gratitude + sign-off
```

---

## Real Message Samples (from Jamie)

### Sample 1 — Flatiron Health (Talent role, found contact on LinkedIn)
> Hi Katherine, this is Jamie! I came across a Talent Engagement role at Flatiron
> and saw you work there. I'd love to connect and learn about your extensive
> experience in Talent Development and any insights on the role. I'd really value
> your perspective as someone earlier in my career, thank you!

**What makes it work:** Mentions the specific role, compliments Katherine's experience
area (Talent Development), positions herself as "earlier in career" = humble, genuine.

### Sample 2 — TikTok (PM role, found contact on LinkedIn)
> Hi Yann-Jong, this is Jamie! I came across a Program Manager opportunity at
> TikTok, Seattle and noticed that you work there! Can we connect to learn about
> your experience and any insights you might have about the role and the company?
> Thanks so much, and hope to connect with you personally!

**What makes it work:** Names the specific role + location, asks about both the role AND
the company (broader), warm closing.

---

## Contact Finding Protocol (Step-by-Step for Each Job Pick)

### Who to Find (priority order)
1. **Hiring Manager** — the person this role reports to (most valuable connection)
2. **Team member** — someone on the same People/HR/OD team at the company
3. **Alumni connection** — USC Marshall / Annenberg or Wesleyan alum at the company
4. **Department adjacent** — someone in a related function (L&D, Recruiting, DEIB) who might know about the role

### How to Find Them (Chrome/LinkedIn)

**Search queries to run in Chrome on LinkedIn:**
```
site:linkedin.com/in "{company}" "HR" OR "people" OR "talent" "manager"
site:linkedin.com/in "{company}" "people programs" OR "talent programs"
site:linkedin.com/in "{company}" "USC" OR "Wesleyan" "HR" OR "people" OR "talent"
```

**LinkedIn People Search (if logged in):**
1. Go to company page → People tab
2. Filter by: "HR", "People", "Talent", "L&D", "OD"
3. Look for titles like: "Head of People Programs", "Sr People Programs Manager",
   "Talent Development Lead", "HR Director" (likely hiring manager)
4. Check for USC/Wesleyan connections (LinkedIn shows this)

### What to Extract from Each Contact's Profile
Before drafting, read their profile for:
- **Current title + how long they've been there** (mention if recent: "congrats on the new role!")
- **Something specific they've worked on** (a post, a project, a promotion, a skill)
- **Shared background** (same school, same city, same previous employer, same interest)
- **Their tone** (formal vs casual — match it in the message)

---

## Message Templates (Adapt, Never Copy Verbatim)

### Template A — Role-Specific Contact (someone on the team)
```
Hi {FirstName}, this is Jamie! I came across the {JobTitle} role at {Company}
and noticed you work on the {their team/function} team. {Something specific
about their work — e.g., "Your background in talent development at scale really
caught my eye." OR "I saw your post about {topic} and found it really insightful."}
I'd love to connect and hear about your experience — I'm exploring similar
opportunities and would really value your perspective. Thank you!
```

### Template B — Alumni Connection
```
Hi {FirstName}! I'm Jamie, a fellow {USC/Wesleyan} alum ({graduation year}).
I noticed you're at {Company} working in {their function} — {something specific
about their career path, e.g., "your transition from consulting to in-house
people ops is really inspiring"}. I'm currently looking at a {JobTitle} role
there and would love to connect and learn about your experience. Hope to chat!
```

### Template C — Hiring Manager (more formal, shorter)
```
Hi {FirstName}, I came across the {JobTitle} position on your team at {Company}
and I'm very interested. {One sentence about why the role resonates — tied to
THEIR team's work, not just Jamie's background.} I'd love the opportunity to
connect and learn more about the team's priorities. Thank you for your time!
```

### Template D — Chinese-speaking Contact (bilingual sign-off)
```
Hi {FirstName}, this is Jamie! I saw the {JobTitle} role at {Company} and
noticed you work there. {Something specific about their work.} I'd love to
connect and learn about your experience and any insights on the role. Thank
you so much!
可爱鸟鸟 🐣
```

### Template E — Warm Re-engagement (someone Jamie already connected with)
```
Hi {FirstName}! Hope you're doing well. I wanted to reach out because I noticed
{Company} has a {JobTitle} opening that really aligns with what I'm looking for.
Last time we chatted about {reference previous interaction}, and I'd love to
reconnect and hear any insights you might have. Thanks so much!
```

---

## Draft Quality Checklist (before including in Notion page)

- [ ] Message is ≤ 300 characters (LinkedIn connection request limit) or ≤ 5 sentences (InMail)
- [ ] References something SPECIFIC about the contact (not generic)
- [ ] Does NOT ask for referral directly
- [ ] Mentions the specific role title and company
- [ ] Matches Jamie's warm, genuine tone
- [ ] No typos, no placeholder text (no "XXX" or "{}")
- [ ] If alumni connection exists, it's mentioned
- [ ] Sign-off is natural (not corporate)

---

## Pipeline Integration

### In Step 6 (Notion page creation), the Networking section should include:
1. **Contact table** with Name, Title, Connection Type, LinkedIn URL
2. **Draft message for each contact** (personalized, not templated)
3. **Connection strategy note** — which contact to reach out to first and why
4. **Shared background flags** — any USC/Wesleyan/Portland/shared employer connections

### Multi-Agent Note
The enrichment agent should:
1. Search LinkedIn for contacts (Chrome)
2. Read each contact's profile summary (Chrome get_page_text)
3. Extract 1-2 specific details to reference
4. Draft message using Jamie's formula
5. Verify message length (≤ 300 chars for connection request)

---

## 📋 Update Log

| Date | Action |
|------|--------|
| 2026-03-24 | Created with 5 templates + Jamie's real samples + contact finding protocol. |
