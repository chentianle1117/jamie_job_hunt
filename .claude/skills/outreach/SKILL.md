---
name: outreach
description: >
  Find networking contacts and draft outreach messages for a job Jamie is applying to.
  Use when Jamie says "who should I reach out to?", "find connections", "draft outreach",
  "help me network for this role", or after /tailor is complete.
  Identifies alumni, hiring managers, and team members, then drafts personalized messages.
argument-hint: "<company name and job title, or reference the job being discussed>"
---

## Stage 3: Networking Outreach

You are helping Jamie identify the right people to contact and draft genuine outreach messages.

### Step 1 — Load Context

Read these files:
1. `jamie/outreach_templates.md` — her voice, style guide, message templates by type, quality checklist
2. `jamie/application_tracker.md` — check if you already have contacts at this company
3. `jamie/content_library.md` — self-intro versions and "why this company" building blocks

### Step 2 — Identify the Target

From `$ARGUMENTS` or the current conversation, confirm:
- **Company name**
- **Job title**
- **Location** (matters for the Portland angle in messages)
- **What you know about the role** (from /evaluate or your own research)

### Step 3 — Find Contacts

There are two modes depending on whether Chrome is available:

---

#### MODE A: With Chrome (`claude --chrome` or `/chrome` enabled)

Chrome mode gives direct access to LinkedIn with your logged-in session. This is
much more powerful — full profiles, mutual connections, alumni filters, and message pre-fill.

> **Prerequisites:** Jamie must be logged into LinkedIn in Chrome before starting.
> If LinkedIn shows a login wall or CAPTCHA at any point, STOP and tell Jamie to handle it.

---

**Step 3a — Company People Page Scan**

Goal: Get an overview of who works in People/HR functions at the company.

1. Navigate to `https://www.linkedin.com/company/{company-slug}/people/`
2. `get_page_text` — read the full People directory
3. Look for the keyword filter bar at the top. If available, filter by:
   - "HR" → scan results
   - "People" → scan results
   - "Talent" → scan results
   - "Learning" or "L&D" → scan results
4. From the results, build a shortlist of 5-8 names with their titles
5. Categorize each as: **hiring manager** (Director/VP/Head of People), **team member**
   (same function as the role), **recruiter**, or **adjacent** (DEIB, Recruiting, etc.)

Report to Jamie:
```
Found [X] People/HR staff at [Company]:
- [Name] — [Title] — likely hiring manager
- [Name] — [Title] — same team
- [Name] — [Title] — recruiter
...
```

---

**Step 3b — Alumni Connection Search**

Goal: Find USC or Wesleyan alumni at the company (warmest connection path).

1. Navigate to:
   `https://www.linkedin.com/search/results/people/?keywords={company name}&schoolFilter=%5B%2217971%22%5D`
   (17971 = USC's LinkedIn school ID)
2. `get_page_text` — read search results
3. For each result, note: name, title, whether they're at the target company
4. Repeat for Wesleyan:
   `https://www.linkedin.com/search/results/people/?keywords={company name}&schoolFilter=%5B%2218057%22%5D`
   (18057 = Wesleyan's LinkedIn school ID)
5. If no alumni found at the company, try broader:
   - USC alumni in same CITY who work in HR/People (potential warm intro path)
   - Search: `https://www.linkedin.com/search/results/people/?keywords=HR people&schoolFilter=%5B%2217971%22%5D&geoUrn=%5B%22103644278%22%5D`
     (geoUrn for US — adjust for Portland/Seattle/NYC as needed)

Report to Jamie:
```
Alumni search:
- USC: [X found / none at this company]
- Wesleyan: [X found / none at this company]
- Nearest alumni: [Name] at [nearby company] — could be warm intro path
```

---

**Step 3c — Check for 2nd-Degree Connections**

Goal: Find people Jamie is already connected to who know someone at the company.

1. Navigate to:
   `https://www.linkedin.com/search/results/people/?keywords={company name}&network=%5B%22S%22%5D`
   (network=S filters to 2nd-degree connections only)
2. `get_page_text` — read results
3. For each 2nd-degree connection, note:
   - Their name and title
   - The mutual connection(s) shown (this is who Jamie knows that knows them)
4. Flag any mutual connections you have actually interacted with (check application_tracker.md)

This is valuable because you can ask the mutual connection for an introduction —
much warmer than a cold connection request.

Report:
```
2nd-degree connections at [Company]:
- [Name] ([Title]) — mutual: [your connection name]
- [Name] ([Title]) — mutual: [your connection name]
→ Recommendation: Ask [mutual connection] for an intro to [best contact]
```

---

**Step 3d — Deep Profile Read (for top 2-3 contacts)**

Goal: Extract specific, personal details to make outreach messages genuine.

For each of the top 2-3 contacts from Steps 3a-3c:

1. Navigate to their LinkedIn profile URL
2. `get_page_text` — read the FULL profile
3. Extract and note:

   **Professional details:**
   - Current title + start date (how long at the company)
   - Previous company/role (career trajectory — did they come from consulting? startup? big tech?)
   - Key skills or endorsements
   - Any published articles or featured posts

   **Personal/connection details:**
   - Education: USC? Wesleyan? Same city? Overlapping graduation years?
   - Location: Portland? Seattle? Same area as Jamie?
   - Recent activity: Did they post about a conference, a company event, a milestone?
   - "About" section: Any personal values, interests, or tone indicators?
   - Volunteer experience or causes (shared values?)

   **Tone indicators:**
   - Is their profile formal (corporate headshot, buttoned-up summary) or casual
     (first-person, emoji, personal stories)?
   - Recent posts: professional tone or conversational?
   - This determines whether your message should be more formal (Template C) or
     warm/casual (Template A/B)

4. For each contact, write a **1-sentence personalization hook**:
   - GOOD: "I noticed you transitioned from consulting to in-house People Ops — I'm on a similar path"
   - GOOD: "Your recent post about manager training resonated with my experience at NextGen"
   - GOOD: "Fellow USC Trojan! I'm also in Org Psych and loved seeing your career path"
   - BAD: "Your impressive career trajectory has been inspiring" (generic, could apply to anyone)
   - BAD: "I admire your leadership in the people space" (flattery, not specific)

---

**Step 3e — Draft Personalized Messages Using Profile Data**

For each contact, draft a message that incorporates what you learned from their profile.
Select the template from `jamie/outreach_templates.md` but **customize it** with the
personalization hook from Step 3d.

**LinkedIn connection request (MUST be under 300 characters):**
```
Hi [Name], this is Jamie! [1 specific detail from their profile — e.g., "I saw you
also studied org psych" or "Your move from consulting to People Ops resonates with
my path"]. I came across the [Role] at [Company] and would love to connect. Thank you!
```
(Draft in first person as Jamie — "I came across...", "my path", etc.)

Count the characters. If over 300, trim — cut the middle, keep the specific detail and the ask.

**Follow-up email (if hiring manager or already connected):**
Use the Virtual Coffee Request or Post-Application email template from outreach_templates.md,
but weave in:
- The specific detail from their profile (Step 3d)
- Something about Jamie's experience that MIRRORS their career path
- The Portland/relocation angle if relevant
- A reference to the company's mission or recent news

---

**Step 3f — Pre-Fill Messages in LinkedIn (optional, if you request)**

If you say "go ahead and pre-fill" or "set up the messages":

1. Navigate to Contact 1's LinkedIn profile
2. Click the **"Connect"** button
3. If a modal appears with "Add a note" option, click it
4. Type the drafted connection request message into the text field
5. **STOP.** Do NOT click "Send" or "Send now."
6. Tell Jamie: `"Message pre-filled for [Name]. Text: [show the message]. Review and press Send when ready."`
7. Wait for Jamie's confirmation before moving to the next contact

Repeat for Contact 2 and Contact 3.

> **CRITICAL:** Never click Send. Never click "Send without a note."
> If the Connect button is grayed out (already connected, or "Follow" only), tell Jamie.
> If LinkedIn shows a weekly connection limit warning, stop and report it.
> If CAPTCHA appears, stop and tell Jamie to complete it manually.

---

#### MODE B: Without Chrome (WebSearch fallback)

Use WebSearch when Chrome is not available:

**Priority 1 — Alumni connections:**
```
site:linkedin.com/in "{company}" "USC" OR "University of Southern California"
site:linkedin.com/in "{company}" "Wesleyan" OR "Wesleyan University"
```

**Priority 2 — Hiring manager / team members:**
```
site:linkedin.com/in "{company}" "people" OR "HR" OR "talent" "manager" OR "director"
site:linkedin.com/in "{company}" "people programs" OR "talent development" OR "L&D"
```

**Priority 3 — Department-adjacent contacts:**
```
site:linkedin.com/in "{company}" "recruiting" OR "DEIB" OR "employee experience"
```

---

For each contact found (either mode), note:
- Name, current title, how long at the company
- Connection type: alumni / team member / hiring manager / adjacent
- Anything specific from their profile (recent promotion, shared interest, mutual connection, etc.)

### Step 4 — Check for Existing Connections

Cross-reference contacts against `jamie/application_tracker.md`:
- Have you already reached out to anyone at this company?
- Do you have any existing LinkedIn connections there?
- Flag any "Connected" or "Reached out" entries for this company

### Step 5 — Draft Messages

For each contact (aim for 2-3), draft a message using the appropriate template from
`jamie/outreach_templates.md`:

**Template selection:**
| Contact type | Template to use |
|---|---|
| USC alum | USC Alumni connection request |
| Wesleyan alum | Wesleyan Alumni connection request |
| MAPP (Org Psych program) alum | MAPP Alumni connection request |
| Hiring manager | Post-Application detailed email OR Hiring Manager connection request |
| Team member | Hiring Manager / Team Member connection request |
| Already connected | Follow-Up After Connecting template |
| Has mutual connection | Mutual Connection Introduction Request |
| 2nd-degree (mutual connection found) | Ask mutual for intro (Mutual Connection Introduction Request) |

**In Chrome mode:** You already have profile data from Step 3d. Use the personalization
hook you wrote for each contact. The message should feel like Jamie actually read their
profile — because you did.

**Personalization checklist (for each message):**
- [ ] References ONE specific thing from their profile (not their title — something personal)
- [ ] Mentions the specific role title and company
- [ ] If alumni: mentions the school + a shared interest or program
- [ ] If 2nd-degree: mentions the mutual connection by name
- [ ] If they posted recently: references the post topic naturally
- [ ] If career path similarity: draws the parallel ("I'm on a similar path — from consulting to in-house OD")
- [ ] Matches their tone (formal profile = formal message; casual profile = warm message)

**Message rules (from your outreach style):**
- LinkedIn connection requests: MUST be under 300 characters
- Reference something SPECIFIC about the contact (not generic)
- Do NOT ask for referrals in the first message
- If alumni connection exists, ALWAYS mention it
- Warm and genuine tone — not corporate, not desperate
- Short: 3-4 sentences max for LinkedIn, 1-2 short paragraphs for email
- End with gratitude and openness, not a hard ask

**The anti-cliche rule:**
Your biggest complaint is messages that sound too purposeful or over-eager. Avoid:
- "I'd love to pick your brain"
- "I'm SO passionate about [exact JD phrase]"
- "I was THRILLED to discover this opportunity"
- "Your impressive career trajectory"
- Generic flattery that could apply to anyone

Instead: be specific, be brief, sound like a real person writing to another real person.

**Examples of profile-informed personalization (GOOD):**
- "I saw your post about scaling manager training across 5 offices — I did something similar at Vestas (12 senior leaders → 23 locations)"
- "Fellow MAPP alum! Your pivot from research to People Ops really resonates — I'm navigating a similar shift"
- "I noticed you joined [Company] from Deloitte Human Capital — I'm exploring a similar move from OD consulting"
- "Your About section mentions you value data-informed people decisions — that's my exact approach (300+ case audits, SPSS)"

**Examples of what NOT to do (BAD):**
- "I noticed your extensive experience in the people space" (could say this about anyone)
- "Your career journey is truly inspirational" (empty flattery)
- "I'm reaching out because I'm passionate about people operations" (about the sender, not about them)

### Step 6 — Build Outreach Strategy

Recommend a contact order:

```
## Outreach Plan for: [Company] — [Job Title]

### Contact 1: [Name] — [Title] — [Connection Type]
**Why first:** [e.g., "USC alum, strongest warm connection path"]
**LinkedIn URL:** [if found]
**Message type:** LinkedIn connection request (< 300 chars)

> [Draft message]

**Character count:** [X]/300

---

### Contact 2: [Name] — [Title] — [Connection Type]
**Why:** [e.g., "Likely on the same team, can give insider perspective"]
**Message type:** LinkedIn connection request

> [Draft message]

---

### Contact 3: [Name] — [Title] — [Connection Type]
**Why:** [e.g., "Hiring manager — reach out AFTER connecting with Contact 1"]
**Message type:** Post-application email (send after applying)

> [Draft message]

---

### Outreach Sequence
1. Send connection request to [Contact 1] — today
2. Send connection request to [Contact 2] — today
3. Apply to the role — today or tomorrow
4. If [Contact 1] accepts, send follow-up message requesting 15-min chat — wait 1-2 days
5. Send email to [Contact 3] (hiring manager) — after applying, attach resume
```

### Step 7 — Portland Angle

If applying to a Portland-area company, you have a powerful personal angle:
"My husband and I are moving back to Portland" (or already in Portland).
Suggest where to weave this into messages — it signals local commitment and is a
genuine conversation starter, especially for hiring managers concerned about relocation.

### Important Notes
- If no contacts are found via WebSearch, say so honestly. Not every company will have
  discoverable LinkedIn contacts. Suggest alternative approaches (check company About page,
  look for team blogs, search for conference speakers from that company).
- You may ask to revise messages multiple times. Stay patient — this is the most
  personal part of the process and getting the tone right matters.
- Never fabricate a contact. If you're not sure someone works there, say "found via LinkedIn
  search — verify before sending."
