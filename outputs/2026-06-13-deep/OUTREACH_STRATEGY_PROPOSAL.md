# Jamie Cheng — Automated Outreach Strategy Proposal

> **Status: RESEARCH + PROPOSAL ONLY.** Nothing in this document has been sent, drafted into Gmail/LinkedIn,
> or committed as an outgoing message. Every template below is a *proposal for David/Jamie to approve*.
> The whole point is to design a system good enough that Jamie would be *proud* to press send — and then
> to put a hard human-approval gate in front of every actual send.
>
> **Author:** Outreach Research Agent · **Date:** 2026-06-13
> **Evidence base:** Jamie's real Gmail threads (`jamiecheng0103@gmail.com`, read-only) + her live LinkedIn
> message history (CDP-9222 authenticated Chrome) + the corpus files in `oracle-job-search/jamie/`.
> **Governing rule:** `JAMIE_FEEDBACK_RULES.md` §0 (NO FABRICATION) outranks everything here.

---

## 0. What I actually read (provenance)

**Corpus files (full read):** `outreach_templates.md`, `outreach_patterns.md`, `jamie_voice_corpus.md`,
`email_style_signature.md`, `JAMIE_FEEDBACK_RULES.md`, `oracle-job-search/CLAUDE.md`.

**Live Gmail threads (read in full, verbatim):**
- C1 / Blake Haggerty — `Talent & Workplace Coordinator at C1` (thread `19e2263aa1e498ae`, 4 msgs)
- Interface / Julie Ho + Pia Sahni (thread `19e8f5feb1b4f9e4`, 18 msgs)
- Nike / Alison Daugherty (thread `19ca44400d956e83`, 27 msgs)
- Boly:Welch / Corbin C (thread `19e4761e88bb78ce`, 11 msgs)
- Boly:Welch / Cory Mlady via Tiffanie Clifford intro (thread `19d797aea6bd8b76`, 8 msgs)
- Morgan Stanley / Edward Lee (recruiter), sourced via Helen Yang (thread `19db5e9e01442ca5`, 7 msgs)
- EY / Riddhi Mandavia (thread `19cb8174e6b6dd15`, 17 msgs)
- Flatiron / Jiun Kimm (thread `19d3fecce7d3ccc6`, 3 msgs)
- Morgan Stanley / Helen Yang (thread `19d874cba62b6391`, 2 msgs)

**Live LinkedIn message threads (read in full, verbatim):** Kell Ording (Articulate), Christina Spoor
(Bio-Techne), Danielle May (Autodesk), Trick Sullivan (BCG), Sasha Olson, Dieuwertje Conrad (Mercer),
Shannon White-Deane, Phoebe Chuang (Bank of China), Sandra Owen (CampusPoint). Plus the full conversation
list (20 active threads, reply-state read from the preview line — "You:" prefix = Jamie sent last).

This is **first-party reply data**, not best-practice guesswork. The single most important thing I learned
is structural and is not in any corpus file (see §1.0).

---

## 1. Evidence base — what actually worked, what actually failed

### 1.0 THE BIG STRUCTURAL FINDING (read this first)

**The email corpus is the *back half* of the funnel; the cold first-touch lives on LinkedIn.** Almost every
"successful email" the voice spec cites (EY/Riddhi, Flatiron/Jiun, MS/Helen, MS/Edward) *opens at the
"thanks again for agreeing to chat" stage* — i.e. the cold contact already happened on LinkedIn and email
only carried the warm continuation (scheduling, resume hand-off). Concretely:

- **EY / Riddhi**, msg 1: *"Thanks again for agreeing to chat with me about your experience in people
  consulting at EY."* → the win happened *before* this email.
- **Flatiron / Jiun**, msg 1: *"I'm excited to hear that you'd be open to connecting over a virtual coffee
  chat sometime!"* → again, already-agreed.
- **MS / Helen**: only 2 msgs, **both from Jamie** — Helen never replied *in email*; instead Helen
  **forwarded Jamie's resume to recruiter Edward Lee**, who then cold-emailed Jamie. So "MS/Helen" was a
  **warm intro / referral**, not a cold email that got a reply. (The voice spec mislabels this as a
  cold-email success — correcting it here.)

**Implication for automation:** the system must treat **LinkedIn as the cold first-touch channel** and
**email as the warm-continuation channel**, and it must *measure replies at the LinkedIn layer*, because
that's where the actual conversion happens. Optimizing email openers in isolation optimizes the wrong step.

### 1.1 The wins, and their common DNA

| Recipient / Company | Channel of first-touch | Type | Outcome | The hook that worked |
|---|---|---|---|---|
| **Blake Haggerty / C1** | **Cold email** (found email online) | Pure cold | Reply in **~5 hrs**, offered a chat (despite calling her "overqualified") | Seasonal opener + transparency ("came across your email online") + "wear a lot of hats" job-texture + **Portland-move anchor** + resume attached |
| **Shannon White-Deane** | LinkedIn (she reached out first re: ODN) | Inbound→converted | In-person coffee scheduled | Jamie named something **specific & true**: *"I saw that you work as a certified coach in the Clifton Strengths space? That's wonderful work!"* + **Boise = on her cross-country route** coincidence |
| **Phoebe Chuang / Bank of China** | (LinkedIn/recruiter) | Warm | Interview being scheduled; personal coffee chat agreed | Specific callback to the call (*"supporting two areas within Employee Management… across different countries"*) + **同鄉人 bilingual warmth** (same hometown) |
| **Alison Daugherty / Nike** | Email via **Amy Rapp warm intro** | Warm intro | Coffee chat → Alison forwarded resume to TA partner → ongoing | *"I believe Amy Rapp reached out to you on my behalf"* (social proof) + Portland move + concrete time windows |
| **Cory Mlady & Corbin C / Boly:Welch** | Email via **Tiffanie Clifford warm intro** | Warm intro | Both scheduled calls | Tiffanie vouched (*"a pleasure to have on a team"*) + Jamie's warm, low-friction scheduling |
| **Julie Ho / Interface** | Inbound via **Pia Sahni referral** | Warm intro | 1st interview → take-home → COO round | Honest reframe (*"I've transitioned away from direct sales… open conversation about where I fit"*) — truth over keyword-matching, and it advanced |
| **Riddhi Mandavia / EY**, **Jiun Kimm / Flatiron**, **Edward Lee / MS** | LinkedIn cold → email warm | Mixed | Coffee chats / recruiter calls | First-touch on LinkedIn; email sustained it |

**The common DNA of every win (in priority order of leverage):**

1. **A real, time-stamped personal anchor.** The **Portland move** ("my husband and I are moving to Portland
   at the end of this month") appears in *every* successful cold/warm email. The **Boise route coincidence**
   converted Shannon. The **同鄉人 / same-hometown** note warmed Phoebe. These are *true, specific, and
   non-transactional* — they make the reach feel like a person, not a pipeline.
2. **Social proof when available.** "Amy Rapp reached out on my behalf," "Tiffanie connected us," "Pia
   referred me." Warm intros convert at a *dramatically* higher rate than cold (see §1.3).
3. **One specific, TRUE detail about the recipient.** Shannon's Clifton Strengths coaching. Not "your
   impressive career." Not "your experience in HRBP" (too generic — that one *failed*, see §1.2).
4. **Transparency about the cold reach.** "Apologies if this is a bit out of the blue, but I came across
   your email online." Naming the awkwardness disarms it.
5. **Job-level texture, not title inflation.** "I wear a lot of hats — running cross-functional programs,
   coordinating vendors, supporting onboarding, and building feedback loops end-to-end." Concrete > grand.
6. **A concrete, low-friction ask with real time windows.** "Friday May 15th 10am or 11am PST; Monday 9–2."
   Never an open-ended "let me know your availability."
7. **Warm, human sign-off + em-dashes.** "Warmly, Jamie Cheng." Occasional 😊 / ✌️ in the sign-off only.

**The canonical best example — C1 / Blake (the ONLY fully-captured pure-cold-email win), verbatim:**

> Hi Blake,
> This is Jamie—I hope you're doing well as the roses start to bloom in Portland!
> Apologies if this is a bit out of the blue, but I came across your email online and wanted to reach out
> personally. I recently applied for the Talent & Workplace Coordinator role at C1, and I wanted to share a
> bit more about myself in case the application alone doesn't quite capture the full picture—and hopefully
> get a chance to connect with someone on the team along the way.
> I'm currently working as a program enablement manager where I wear a lot of hats—running cross-functional
> programs, coordinating vendors, supporting onboarding, and building feedback loops end-to-end. Earlier in
> my career I worked at a fintech startup, where I got to turn ambiguity into concrete solutions… As someone
> with a background in organizational psychology and work experience in HR and the people experience space,
> I'm also genuinely curious to learn more about what the current talent experience looks like at C1 and
> where I might jump in to help create data-driven, systematic solutions.
> On a personal note: my husband and I are actually moving to Portland at the end of this month and will be
> settling there for the foreseeable future, so I was really excited to find out that this role is based in
> Portland!
> I've attached my resume. Thanks so much for your time, Blake—I hope to connect soon!
> Warmly, Jamie Cheng

Blake's reply (5 hours later): *"Thank you for reaching out. To be completely transparent, you seem
potentially overqualified for this role. With that said, I am happy to chat… When is a good time to connect?"*

### 1.2 The failures, and their shared anti-pattern

**Three LinkedIn cold first-touches got ZERO reply.** All three are nearly word-for-word identical, and the
match to a generic template is exact:

> **Kell Ording (Articulate, May 8):** "Hi Kell! This is Jamie, and I applied to the Training Program Manager
> role at Articulate and saw that you work there. I was wondering if, by any chance, you might have some
> insights about the role? I'd also love to hear about your work experience there over a quick coffee chat.
> Let me know, thanks!"
>
> **Christina Spoor (Bio-Techne, Apr 23):** "Hi Christina, this is Jamie! I recently applied for the HR
> Specialist role at Bio-Techne and noticed your experience in HRBP. I'd love to connect and learn more
> about your experience and any insights you might have on the role or team. Thank you so much—I look forward
> to connecting!"
>
> **Danielle May (Autodesk, Apr 22):** "Hi Danielle, this is Jamie! I recently applied for the Program
> Manager role at Autodesk and noticed your experience in program management at the company. I'd love to
> connect and learn more about your experience and any insights you might have on the role or team. Thanks
> so much—really appreciate it!"

**Why they died (the anti-pattern, in order of damage):**

1. **No personal anchor.** No Portland move, no coincidence, no human detail. The *single most powerful
   element in every win* is **absent in every failure**.
2. **Fake-specific "detail" about the recipient.** "noticed your experience in HRBP" / "in program
   management at the company" is *category recognition*, not a real observation. It reads as a mail-merge
   field, because it is one.
3. **Transactional ask up front.** "any insights you might have on the role or team" = asking the stranger
   to do unpaid labor for Jamie's application. Compare Shannon, where Jamie *gave* a compliment first.
4. **Interchangeable.** Swap the name/company and the message is identical. Recipients can smell a blast.

**Caveat (intellectual honesty):** the generic opener is **high-variance, not always-fatal.** Dieuwertje
Conrad (Mercer) got the *same* generic template (*"I came across a Talent & Rewards Consulting opportunity
at Mercer and noticed that you work there. Can we connect to learn about your experience and any insights…"*)
and **did reply**, offering a recruiter intro — but the thread then died because the role was already filled.
So generic openers occasionally land when the recipient happens to be receptive; they just convert far worse
and produce nothing memorable. We should not ship them.

### 1.3 Reply-rate read (observable, not estimated)

From the threads I could directly observe:
- **Warm intros (Amy Rapp→Nike, Tiffanie→Boly:Welch, Pia→Interface, Helen→MS):** ~**100%** progressed to a
  chat or interview. Every single warm intro converted. This is the highest-leverage channel by a wide margin.
- **Pure cold *email* with full personalization (C1/Blake):** converted (n=1 captured, but a clean win).
- **Cold *LinkedIn* with a real specific hook + personal anchor (Shannon):** converted to in-person meet.
- **Cold *LinkedIn* with the generic template (Kell, Christina, Danielle):** **0/3 replied.** Dieuwertje
  replied but didn't convert. Call it ~**1/4 reply, 0/4 conversion** for the generic pattern.

**Takeaway:** the ranked priority for the engine is **(1) get a warm intro if any path exists → (2) if cold,
personalize hard with a true anchor → (3) never ship the generic template.**

---

## 2. Diagnosis — exactly why the current automated drafts fail

The autopilot drafts fail in three distinct, fixable ways:

### 2.1 They reproduce the dead generic template
The current drafts collapse to the Kell/Christina/Danielle skeleton: *"I recently applied for [Role] at
[Company] and noticed your experience in [function]. I'd love to connect and learn more about your experience
and any insights you might have on the role or team."* This is the **exact** message that got 0/3 replies.
It has no anchor, no real detail, and a transactional ask. **Ban it.**

### 2.2 The fabrication failure mode (the most dangerous)
The drafts sometimes invent recipient-specific research Jamie never did — e.g. *"I've followed how the
organization has…"* This violates **RULE 0 (NO FABRICATION)**, which outranks everything. It is dangerous
beyond being cliché: if a recipient replies *"oh, what did you think of our recent X?"*, Jamie is caught
flat in a lie she didn't author. The corpus already flags this verbatim:
- `JAMIE_FEEDBACK_RULES.md` §7: *"Do NOT fabricate that Jamie 'followed how the organization has…' — she
  didn't. Never claim research/following she didn't do."*
- The fix is not "tone it down" — it's a **hard verifiability gate**: every recipient-specific clause must
  point at a real artifact (a real post, a real shared school, a real role on their live profile, a real
  line of the JD). No artifact → the clause is deleted, not softened.

### 2.3 Missing the real context that makes Jamie's reaches land
The drafts omit the two things that actually convert:
- **The personal anchor** (Portland move / a true geographic or biographical coincidence). It's in every win
  and absent from every failure, yet the templated drafts drop it.
- **One TRUE specific detail about the recipient** pulled from their *live* profile (their actual current
  title, a real post, a genuine shared background). The drafts substitute a category label ("HRBP experience")
  for a real observation.

### 2.4 Banned-phrase list (hard filter — auto-reject any draft containing these)
From `email_style_signature.md`, `outreach_templates.md`, and the observed failures:
- "I'd love to pick your brain"
- "I'd love to learn more" *as a standalone sentence*
- "any insights you might have on the role or team" (the failure fingerprint)
- "I came across your profile" *without a specific true detail immediately after*
- "I've followed how [the org / your work] has…" (**fabrication**)
- "I am passionate about…", "I have always believed…", "dream company", "perfect fit"
- "synergy", "leverage" (as a standalone verb), "move the needle", "circle back"
- "$340K / 17 launches" (**banned hallucinated metric** — use "78% program enrollment rate")
- Any clause that re-labels ODN Oregon as "community building / ERG / network growth" (it is **OD diagnostic
  consulting** — see §0.2 of the rules).

---

## 3. Targeting — who to reach per role, and how to verify

### 3.1 Priority order of recipient (per role)
Grounded in what converted for Jamie:

1. **A warm-intro broker** (highest leverage — ~100% conversion). Before any cold reach, check: does Jamie
   (or David) know anyone at the company, or anyone connected to someone there? Her wins (Nike, Boly:Welch,
   Interface, MS) were *all* warm intros. **This is the first question the engine asks, every time.**
2. **A future peer / practitioner on the team** (IC or manager in the same People/HR/OD/L&D function). This
   is the *peer-curiosity* lane the rules favor — "as a fellow People Ops practitioner, what does it look
   like day-to-day?" Lower stakes than the hiring manager, high willingness to chat.
3. **The hiring manager** (the person the role reports to). Highest value if reached, but use the more
   deferential template (§5).
4. **A recruiter / TA partner** (esp. agency recruiters like Boly:Welch, CampusPoint — they *want* to place
   people and replied warmly to Jamie). Great for market intel + getting into an ATS.
5. **Alumni** — USC Marshall/Annenberg (MAPP/Org Psych) or Wesleyan — *only if real*. A true alumni tie is a
   legitimate warm-open; a fabricated one violates RULE 0.

### 3.2 Verification (HARD RULE — mandatory, no exceptions)
`outreach_templates.md` Step 0 and the rules are explicit, because the system got this wrong twice (Jessica
Redeman had left Roivant; Kaitlyn Major-Hale is at Google, not Built In):

- **Open the recipient's *live* LinkedIn profile** (not a search-result snippet, not a cached guess).
- **Confirm their *current* employer and title match the target company/role.** Read the "current position"
  block, not just the headline.
- If current employment **cannot be confirmed → do NOT draft.** Flag to Jamie: "couldn't verify X still
  works at Y — skipping." This is a feature.
- The engine must **store the verification artifact** (profile URL + the current-title string it read + a
  timestamp) alongside the draft, so the human gate can see *why* the system believes this is the right person.

---

## 4. Personalization engine — real, verifiable context only

### 4.1 The per-recipient "evidence packet" the engine must assemble *before* drafting
For each verified recipient, pull and store these fields. **Each is either a real artifact or it is left
empty — never invented.**

| Slot | Source | Verifiability rule |
|---|---|---|
| `current_title` + `current_company` | Live LinkedIn current-position block | Must be read from the live profile this session |
| `tenure` | Live LinkedIn ("X yrs Y mos") | Optional; only if shown. Enables "congrats on the new role" if < ~6 mo |
| `one_true_detail` | A *real* recent post, a listed project, a certification, a prior shared employer, a shared school | Must quote/point to the actual artifact. If none found → leave empty and **drop the personalization clause** (do not fabricate) |
| `alumni_tie` | Live profile education section | Only "fellow USC/MAPP/Wes alum" if the profile actually shows it |
| `warm_intro_broker` | Jamie's/David's network, mutual LinkedIn connections | Name a real person who agreed to vouch; else empty |
| `jd_responsibility` | The actual JD text | Quote/paraphrase a *real* responsibility line — NOT company holding-structure |
| `personal_anchor` | Jamie's true situation | Portland move (still true), a real route/location coincidence, 同鄉/shared-language tie — all real |

### 4.2 The hard verifiability gate (RULE 0, enforced mechanically)
Before any draft is shown to the human:
- [ ] Every recipient-specific clause maps to a filled slot above (with its artifact).
- [ ] No clause asserts research/following Jamie didn't do.
- [ ] No banned phrase present (§2.4 filter).
- [ ] JD reference is a real responsibility, not holding-company/subsidiary structure.
- [ ] Jamie-side claims trace to `resume.md` / `content_library.md` / `profile_compact.md`.
- [ ] If `one_true_detail` is empty, the message uses the *role-focused* variant (no fake personal detail).

If any check fails, the draft is **rejected back to the writer with the specific failing clause** — the same
orchestrator quality-gate discipline the rules already mandate for resumes/cover letters.

### 4.3 The "would-Jamie-be-proud" bar
A draft passes only if it would survive Jamie reading it aloud to the recipient on a call. If a line would
make her wince ("I never said that") or cringe (cliché), it fails. This is the subjective gate that sits
*after* the mechanical one.

---

## 5. Voice & templates (PROPOSALS — for David/Jamie to approve, not to send)

> All slots in `{curly braces}` are **filled only from the verified evidence packet (§4.1)**. An empty slot
> means the clause is **removed**, never guessed. These mirror Jamie's real winning structure.

### 5.1 LinkedIn connection note — COLD, with a real detail (≤ 300 chars)
*Use when there's a true `one_true_detail`. This is the Shannon-pattern that converts.*
```
Hi {First}, this is Jamie! {one_true_detail_as_genuine_compliment_or_observation}. I'm exploring
{role_function} roles and {company} caught my eye. I'd love to connect — and {personal_anchor_short}.
```
Worked-from example (Shannon, real): *"I saw that you work as a certified coach in the Clifton Strengths
space? That's wonderful work!"* → real detail, warm, gave before asking.

### 5.2 LinkedIn connection note — COLD, no true detail available (≤ 300 chars)
*Use when no real recipient detail exists. Lean on the role + a real personal anchor — NOT a fake "noticed
your experience" line.*
```
Hi {First}, this is Jamie — {personal_anchor_short, e.g. "I'm moving to Portland this month and exploring
people-team roles here"}. I came across the {role} opening at {company} and would genuinely value connecting
with someone on the team. Hope to chat!
```
> Note: this *still* outperforms the dead template because it carries a true anchor and doesn't fake-flatter.

### 5.3 Post-application cold EMAIL (Jamie's strongest format — the C1/Blake structure, 200–300 words)
*Use when an email address is findable and Jamie has applied. This is the proven pure-cold winner.*
```
Subject: {Role} at {Company} — Jamie Cheng

Hi {First},

This is Jamie — {warm_seasonal_or_situational_opener}.

Apologies if this is a bit out of the blue, but I came across your email online and wanted to reach out
personally. I recently applied for the {Role} role at {Company}, and wanted to share a bit more about myself
in case the application alone doesn't quite capture the full picture.

I'm currently a program enablement manager where I wear a lot of hats — running cross-functional programs,
coordinating vendors, supporting onboarding, and building feedback loops end-to-end. {one_TRUE_JD_tie:
"I was especially drawn to {real_JD_responsibility}, which reminds me of {real_Jamie_experience}."} As
someone with a background in organizational psychology and work in the people-experience space, I'm
genuinely curious how the {team/talent} experience looks at {Company} today.

On a personal note: {personal_anchor — e.g. "my husband and I are moving to Portland this month and I was
excited this role is based here!"}

I've attached my resume. Thanks so much for your time, {First} — I hope to connect soon!

Warmly,
Jamie Cheng
```

### 5.4 Peer practitioner email (already-applied, IC/manager)
*From `outreach_templates.md` (Jamie-edited). Role-focused, peer-curiosity, concrete timeframe.*
```
Hi {First},

I hope you're doing well! I recently applied for the {Role} role at {Company} and wanted to reach out
personally.

I was particularly drawn to {ONE real responsibility from the JD — e.g. "the employee-relations complexity
that needs careful handling and cross-functional collaboration — it reminds me of the work I did at Vestas"}.
As a fellow People Operations practitioner, I'd love to hear what it looks like day-to-day on your team —
what are some exciting opportunities, and some of the challenges?

I have some time in the next two weeks if you're free for a quick chat. Thank you so much — I hope to
connect soon!

Warmly,
Jamie Cheng
```

### 5.5 Senior leader (Head of People / VP) email
*Shorter, more deferential. Leads with background + "strategic lever" line. No org-structure talk.*
```
Hi {First},

I hope you're doing well! I recently applied for the {Role} role at {Company} and wanted to reach out
personally.

I'm a People & OD professional with a background in organizational psychology and hands-on experience across
program management, employee experience, and cross-functional HR work. I'm drawn to organizations where
People is a strategic lever, not just operational — and from what I've seen of {Company}, it sounds like
that's the case there.

I'd be honored to connect — no agenda beyond learning about the team's challenges and exciting opportunities.
I have some time in the next two weeks if you're open to a brief chat.

Thank you so much for your time!

Warmly,
Jamie Cheng
```

### 5.6 Warm-intro reply (when a broker connects Jamie — her ~100% lane)
*Mirror her real Nike/Boly:Welch replies: thank the broker, warm intro to the new person, real anchor,
concrete windows.*
```
Thank you so much for connecting us, {Broker}!

Hi {First}, lovely to e-meet you! {personal_anchor — Portland move etc.} and I've been exploring
opportunities in {function}. I'd love to learn about your experience{/the team} if you're open to a video
chat in the next two weeks. Would {2–3 concrete windows} work? Happy to adjust to your schedule.

Looking forward to connecting!
Warmly, Jamie Cheng
```

### 5.7 Follow-up (existing thread, no reply ~5–7 days, < 80 words)
*Jamie's real C1 follow-up style — light, no new pitch, no guilt.*
```
Hi {First}, hope you had a great {weekend/week}! Just following up to see if you'd be free for a quick chat
sometime this week — my {days} look pretty open. Looking forward to connecting!
Best, Jamie
```

### 5.8 Voice rules baked into every template
- Em-dashes are load-bearing — keep them. · Tricolon ("X, Y, and Z") for skill clusters.
- Sign-off: **"Warmly,"** for warm/personal cold reaches; **"Best,"** for follow-ups/scheduling;
  **"Sincerely,"** only for the most formal first contact. Occasional 😊/✌️ in sign-off only.
- Chinese-speaking contact: warmer tone OK; bilingual sign-off "可愛鳥鳥 🐣" or a genuine Chinese line like
  Phoebe's *"今天真的也很高興認識妳"* — **only if Jamie would actually write it to that person.**
- **Never** a referral ask in message 1. Build the relationship first.
- Plain text only in any form field; formatting belongs in the attached PDF (`feedback_clean_plaintext`).

---

## 6. Channel & sequencing

### 6.1 Channel decision (from the evidence)
```
Is there a warm-intro path (mutual connection / known broker)?
  └─ YES → request the intro first (highest conversion). Use §5.6 once connected.
  └─ NO  → Is a real email address findable (e.g., pattern from company domain, or listed)?
            ├─ YES → cold EMAIL §5.3 (Jamie's strongest cold format — C1/Blake proved it)
            └─ NO  → LinkedIn connection note: §5.1 if a true detail exists, else §5.2
```
- **LinkedIn connection note** for first-touch when no email exists (≤ 300 chars, must clear the gate).
- **Email** is preferred for the post-application cold reach — it carries more context and Jamie's best
  format lives there.
- **InMail** only as a last resort (costs a credit, lower trust); same content as §5.1/5.2 but can run longer.

### 6.2 Cadence (conservative — Jamie's real rhythm)
- **First touch** → **one** follow-up after **5–7 days** (§5.7) → then **stop.** Jamie followed up *once*
  (Blake, Cory) and then let it rest. No third chase.
- Warm intros: respond **same-day** (she replied to Edward Lee within the hour; that responsiveness matters).
- **Max ~2 touches per recipient, ever.** Persistence belongs in *applications*, not in pestering people.

### 6.3 Volume guardrail
Jamie's win rate comes from *quality*, not blast volume. Cap automated cold first-touches at a small,
human-approved batch per run (proposal: **≤ 5–8 per night**, each individually approved). The generic-blast
failure mode (Kell/Christina/Danielle were all rapid-fire one-liners) is exactly what we're eliminating.

---

## 7. Timing & per-role triggers

- **Best send windows (from her successful sends):** weekday mornings, roughly **9 am–12 pm in the
  recipient's timezone** (Blake reply came same evening from an AM-ET send; EY/Flatiron/MS sends cluster
  late-morning ET). Avoid Friday afternoon and weekends for first-touch.
- **Per-role trigger — "right after applying."** Her strongest format *opens* with "I recently applied for
  {Role}." So the natural automation trigger is: **application submitted → within 24–48h, assemble the
  evidence packet and queue an outreach draft for approval.** The application is the legitimizing pretext.
- **Recency trigger:** if the recipient posted recently or just changed roles, fire sooner and use the real
  detail/congrats hook.
- **Respect timezones:** Jamie carefully localized every time ("11 am PST", "9:45 am your time… 11:45 am for
  me"). The engine must compute and state both timezones in scheduling messages.

---

## 8. Measurement — what to track + surface on the dashboard

### 8.1 Per-outreach record (proposed schema, one row per touch)
`recipient_name · company · role · channel(email/LI/InMail) · recipient_title_verified · verify_url ·
verify_timestamp · warm_intro_broker · personal_anchor_used · one_true_detail_used(Y/N) · template_id ·
status(draft→approved→sent→opened→replied→meeting→declined→cold) · first_touch_date · followup_date ·
reply_date · reply_sentiment · outcome · gate_passed(Y/N) · rejected_reasons[]`

### 8.2 The metric that actually matters
- **Reply rate by template + by personalization-depth** (true-detail vs anchor-only vs generic). This is the
  feedback loop that kills bad templates. (Current data: generic ≈ 1/4 reply, 0 convert; personalized ≈
  converts.)
- **Conversion to chat/interview** (the real goal), segmented by channel: warm-intro vs cold-email vs
  cold-LI. Expect warm-intro to dominate — and that should *drive sourcing* toward finding brokers.
- **Gate rejections** (how often drafts fail the verifiability/banned-phrase gate) — a quality canary; rising
  rejections mean the generator is drifting back toward the dead template.

### 8.3 Dashboard surface (for Jamie's quality-check)
Add an **Outreach** panel to `jamie/dashboard.html`:
- A **review queue**: each pending draft shown *in full*, with its evidence packet (verified title + URL,
  the true detail, the anchor) inline, and **Approve / Edit / Reject** controls. Jamie sees exactly what the
  system is claiming and *why* before anything sends.
- A **sent/replied tracker**: status pills per recipient, reply-rate-by-template chart, follow-up-due flags.
- A **"needs human"** lane for anything the gate couldn't auto-verify.

---

## 9. Automation architecture (proposal) — where the human gate sits

```
┌─ DISCOVERY (existing autopilot) ── role + JD captured, application submitted
│
├─ 1. TARGETING agent (haiku)
│     → find candidate recipients (warm-intro broker first, then peer/HM/recruiter/alumni)
│
├─ 2. VERIFICATION agent (haiku, drives CDP-9222 LinkedIn)
│     → open each LIVE profile, confirm current employer+title, store {url, title, timestamp}
│     → unverifiable recipient = DROPPED + flagged (never drafted)
│
├─ 3. EVIDENCE-PACKET agent (haiku)
│     → pull one_true_detail / tenure / alumni_tie / real JD responsibility / personal_anchor
│     → every slot is a real artifact or left empty
│
├─ 4. DRAFT agent (sonnet — judgment/voice)
│     → pick template by channel+seniority (§5), fill ONLY from the packet, Jamie's voice
│
├─ 5. GATE (orchestrator, NON-NEGOTIABLE — RULE 0)
│     → mechanical: verifiability + banned-phrase + sourced-claims + JD-not-structure checks
│     → reject-with-reason back to step 4 until it passes
│
├─ 6. ░░░ HUMAN APPROVAL GATE ░░░  ←—— NOTHING SENDS BEFORE THIS
│     → draft + evidence packet surfaced on dashboard / to David & Jamie
│     → David/Jamie: Approve · Edit · Reject. Default with no answer = DO NOT SEND.
│
└─ 7. SEND (only after explicit approval)
      → email: send from Jamie's own Gmail ONLY with her sign-off (NOTE security rule below)
      → LinkedIn: CDP-9222 send the approved note
      → CAPTCHA / any verification challenge → ALWAYS stop and hand to human (never auto-solve)
      → log to the per-outreach record (§8.1); schedule the single follow-up (§6.2)
```

### 9.1 Hard guardrails (explicit)
- **NOTHING sends without explicit human approval.** The default on silence is *do not send*. This is the
  inverse of the application autopilot's "submit everything" posture — outreach touches real named humans in
  Jamie's name, so it is approval-gated, always.
- **CAPTCHA + send are always gated** (consistent with `feedback_captcha_tab_detach_not_hold` and the
  screenshot-review-before-submit rules).
- **RULE 0 gate runs before the human ever sees a draft** — the human reviews *clean, verified* drafts, not
  raw model output, so their attention is spent on judgment, not error-catching.
- **Verification artifacts travel with every draft** so the human can audit the targeting.
- **Identity/sending-account rule must be resolved (see §10).** Jamie's real outreach goes out as *Jamie*
  from *her* Gmail; David's global security rule says Claude only *sends* from `tianlechen0324@gmail.com`.
  These conflict for live sends — flagged as the top open question.

---

## 10. Open questions for David (decisions needed)

1. **🔴 Sending identity / account (blocker for any live send).** Jamie's authentic outreach must come *from
   Jamie* (her Gmail, her LinkedIn, her sign-off) — that's the whole premise. But the global security rule is
   that Claude only *sends* email from `tianlechen0324@gmail.com`. For automated *sending* (not today —
   later), which is it?
   - **(A)** Approved drafts are placed as **Gmail drafts in Jamie's account** for her to press send herself
     (keeps Claude from sending in her name; safest; *recommended default*).
   - **(B)** Claude sends from Jamie's Gmail *only after per-message human approval* (true automation, but
     crosses the "only send from tianlechen" line — needs your explicit exception).
   - **(C)** LinkedIn-only auto-send (via CDP-9222) + email always left as a draft for Jamie.
   - *Default if no answer: **A** (draft-only; human presses send).*

2. **Volume & approval granularity.** Per-message approval (safest) or per-batch approval of up to N
   pre-vetted drafts per night? (Proposal: per-message until trust is established, then per-batch.)

3. **Warm-intro brokering.** The data says warm intros convert ~100%. Should the engine *actively surface
   intro opportunities* (scan Jamie's + your mutual LinkedIn connections at target companies) and propose
   "ask {broker} for an intro to {person}" as a first move — or stay cold-only for now?

4. **LinkedIn automation risk tolerance.** Driving Jamie's real LinkedIn via CDP to *send* connection notes
   carries a (small) account-safety risk. OK to send LI notes through automation post-approval, or keep
   LinkedIn 100% manual and automate email-drafts only?

5. **Scope of "personal anchor" after the move.** The Portland-move anchor was Jamie's strongest hook but is
   now expiring (she's moved/moving). What replaces it as the default true anchor — "newly based in
   Portland," a faith/values tie for mission-aligned orgs, the cross-country-move story while still fresh?
   Need her steer so the engine doesn't invent one.

---

## Appendix A — Win/loss ledger (verbatim openers, for the template library)

**WINS (quote-grade):**
- C1/Blake — full text in §1.1 (pure cold email; reply in ~5h).
- Shannon — *"I saw that you work as a certified coach in the Clifton Strengths space? That's wonderful
  work!"* (specific true detail) + Boise route coincidence → in-person meet.
- Phoebe/BOC — *"…supporting two areas within Employee Management and collaborating with colleagues across
  different functions and even different countries :) 今天真的也很高興認識妳，尤其又是同鄉人！"* (specific
  callback + bilingual same-hometown warmth) → interview scheduling + personal chat.
- Nike/Alison — *"I believe Amy Rapp reached out to you on my behalf earlier this week…"* (warm intro) +
  Portland move + concrete windows → resume forwarded to TA partner.

**LOSSES (the banned template — 0/3 reply):**
- Kell/Articulate, Christina/Bio-Techne, Danielle/Autodesk — all variants of *"I recently applied for [Role]
  at [Company] and noticed your experience in [function]. I'd love to connect and learn more about your
  experience and any insights you might have on the role or team."* No anchor, fake-specific, transactional.

**EDGE (generic, replied but didn't convert):** Dieuwertje/Mercer — same generic template, got a recruiter-
intro offer, died because the role was already filled. Generic = high-variance, low-yield; do not ship.
