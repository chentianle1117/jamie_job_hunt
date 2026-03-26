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
2. `jamie/application_tracker.md` — check if she already has contacts at this company
3. `jamie/content_library.md` — self-intro versions and "why this company" building blocks

### Step 2 — Identify the Target

From `$ARGUMENTS` or the current conversation, confirm:
- **Company name**
- **Job title**
- **Location** (matters for the Portland angle in messages)
- **What Jamie knows about the role** (from /evaluate or her own research)

### Step 3 — Find Contacts

Search for potential contacts in this priority order:

**Priority 1 — Alumni connections:**
Use WebSearch:
```
site:linkedin.com/in "{company}" "USC" OR "University of Southern California"
site:linkedin.com/in "{company}" "Wesleyan" OR "Wesleyan University"
```

**Priority 2 — Hiring manager / team members:**
Use WebSearch:
```
site:linkedin.com/in "{company}" "people" OR "HR" OR "talent" "manager" OR "director"
site:linkedin.com/in "{company}" "people programs" OR "talent development" OR "L&D"
```

**Priority 3 — Department-adjacent contacts:**
Use WebSearch:
```
site:linkedin.com/in "{company}" "recruiting" OR "DEIB" OR "employee experience"
```

For each contact found, note:
- Name, current title, how long at the company
- Connection type: alumni / team member / hiring manager / adjacent
- Anything specific from their LinkedIn snippet (recent promotion, shared interest, etc.)

### Step 4 — Check for Existing Connections

Cross-reference contacts against `jamie/application_tracker.md`:
- Has Jamie already reached out to anyone at this company?
- Does she have any existing LinkedIn connections there?
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

**Message rules (from Jamie's outreach style):**
- LinkedIn connection requests: MUST be under 300 characters
- Reference something SPECIFIC about the contact (not generic)
- Do NOT ask for referrals in the first message
- If alumni connection exists, ALWAYS mention it
- Warm and genuine tone — not corporate, not desperate
- Short: 3-4 sentences max for LinkedIn, 1-2 short paragraphs for email
- End with gratitude and openness, not a hard ask

**The anti-cliche rule:**
Jamie's biggest complaint is messages that sound too purposeful or over-eager. Avoid:
- "I'd love to pick your brain"
- "I'm SO passionate about [exact JD phrase]"
- "I was THRILLED to discover this opportunity"
- "Your impressive career trajectory"
- Generic flattery that could apply to anyone

Instead: be specific, be brief, sound like a real person writing to another real person.

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

If Jamie is applying to a Portland-area company, she has a powerful personal angle:
"My husband and I are moving back to Portland" (or already in Portland).
Suggest where to weave this into messages — it signals local commitment and is a
genuine conversation starter, especially for hiring managers concerned about relocation.

### Important Notes
- If no contacts are found via WebSearch, say so honestly. Not every company will have
  discoverable LinkedIn contacts. Suggest alternative approaches (check company About page,
  look for team blogs, search for conference speakers from that company).
- Jamie may ask you to revise messages multiple times. Stay patient — this is the most
  personal part of the process and getting the tone right matters.
- Never fabricate a contact. If you're not sure someone works there, say "found via LinkedIn
  search — verify before sending."
