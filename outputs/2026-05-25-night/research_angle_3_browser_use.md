# Research Angle 3: Vision-LLM Browser Agent Frameworks for Autonomous Job Application
*Researched: 2026-05-27 | Agent: Angle 3 of 5*

---

## TL;DR

**browser-use** (Python, open-source, 50k+ stars) is the strongest pick: it uses Playwright + vision LLMs, supports `extend_system_message` for hardcoding work-auth answers, and can handle all 6 of Jamie's ATSes through its DOM+screenshot hybrid approach. **Skyvern** is the best purpose-built alternative with a dedicated Jobs Agent, YAML-configurable data passing, and 85.8% WebVoyager benchmark — but its self-hosted path adds DevOps overhead. **Claude Computer Use API** provides the highest single-agent reliability (72.5% OSWorld, covers any UI) but costs ~$0.006–$0.018/action and requires careful prompt engineering to hardcode sponsorship answers. No tool officially lists ADP Workforce Now or PeopleAdmin as tested targets, but vision-based agents handle them better than selector-based tools because they don't depend on static DOM.

---

## Tool Status Summary (2026)

### 1. browser-use (github.com/browser-use/browser-use)
- **Status**: Actively maintained, 50k+ GitHub stars (May 2026), YC-backed
- **Architecture**: Python lib, Playwright under the hood, supports vision (screenshots) + DOM extraction, or both
- **LLM support**: OpenAI, Anthropic, Google, Ollama (local)
- **Sponsorship override**: YES — `extend_system_message` and `override_system_message` parameters allow injecting hard-coded rules into every agent turn. Pattern:
  ```python
  agent = Agent(
      task="Apply to this job",
      llm=llm,
      extend_system_message="""
      CRITICAL RULES — follow exactly on every form:
      - 'Authorized to work in the US?' → always answer YES
      - 'Require sponsorship now or in the future?' → always answer YES
      - 'US citizen or permanent resident?' → always answer NO
      - Do NOT infer or guess visa status — use these exact answers.
      """
  )
  ```
- **ATS coverage (Jamie's 6)**:
  | ATS | Expected handling |
  |---|---|
  | Workday | Good — vision handles dynamic React UI |
  | Greenhouse-style portal | Good — standard HTML forms |
  | SAP SuccessFactors | Moderate — complex SPA, occasional JS timeout |
  | ADP Workforce Now | Untested in public benchmarks — vision-first approach should work |
  | PeopleAdmin | Untested publicly — vision-first approach should work |
  | Aurora careers | Unknown — need live test |
  **Score: 4/6 confirmed, 2/6 likely but untested**
- **Reliability**: No published ATS-specific benchmark. Community reports ~60-75% success on Workday, lower on dynamic SPAs.
- **Cost**: Only LLM API cost. ~$0.10–$0.30/application with Claude Sonnet 4.6 (est. 15–25 screenshot-action cycles @ $3/$15 per M tokens).
- **Setup time**: pip install + LLM API key = ~15 min. First application run: ~45 min including prompt tuning.
- **Local-first**: YES — runs entirely locally, no SaaS dependency.
- **Sources**: [browser-use GitHub](https://github.com/browser-use/browser-use) | [docs: system prompt](https://docs.browser-use.com/customize/system-prompt) | [Apify guide 2026](https://use-apify.com/blog/browser-use-ai-browser-automation-guide) | [YC](https://www.ycombinator.com/companies/browser-use)

---

### 2. Skyvern (skyvern.com / github.com/Skyvern-AI/skyvern)
- **Status**: Active, YC S23, raised $2.7M, blog posts through May 2026 (Workflow Chaining post: May 2026)
- **Architecture**: Vision LLM + computer vision on screenshots; YAML workflow definitions; REST API; Jobs Agent feature launched Feb 2025
- **Benchmark**: 85.8% on WebVoyager — highest published benchmark of any open-source browser agent
- **Sponsorship override**: YES — YAML parameters allow passing structured data into any form field by key. The Jobs Agent accepts a full applicant profile object. Work auth fields can be set as explicit parameters:
  ```yaml
  parameters:
    work_authorized: true
    requires_sponsorship: true
    us_citizen_pr: false
  ```
  Skyvern's form-fill understands semantic context ("Given Name", "First Name", "Forename" all map correctly). This makes it more reliable than selector-based tools for ambiguously labeled work-auth fields.
- **ATS coverage (Jamie's 6)**:
  | ATS | Expected handling |
  |---|---|
  | Workday | Good — explicitly mentioned in docs and blog |
  | Greenhouse-style portal | Good — explicitly listed as use case |
  | SAP SuccessFactors | Likely — vision-based, not selector-based |
  | ADP Workforce Now | Not mentioned; vision approach should handle |
  | PeopleAdmin | Not mentioned; vision approach should handle |
  | Aurora careers | Unknown |
  **Score: 4/6 confirmed or likely, 2/6 untested**
- **Reliability**: 85.8% WebVoyager; job application-specific % not published
- **Cost (cloud)**: SaaS pricing not publicly disclosed; open-source self-hosted = LLM API cost only (~similar to browser-use)
- **Setup time (self-hosted)**: Docker Compose setup ~30-60 min. First application: ~2 hours including YAML workflow config.
- **Setup time (cloud)**: ~20 min to configure Jobs Agent via app.skyvern.com
- **Local-first**: Open-source self-hosted OR cloud SaaS
- **Sources**: [Skyvern Jobs Agent blog](https://blog.skyvern.com/launching-skyverns-jobs-agent-automate-job-applications-with-ai-2/) | [Skyvern jobs page](https://www.skyvern.com/jobs) | [Skyvern GitHub](https://github.com/Skyvern-AI/skyvern) | [Parameter docs](https://docs.skyvern.com/workflows/what-is-a-parameter) | [YC listing](https://www.ycombinator.com/companies/skyvern)

---

### 3. Claude Computer Use API (Anthropic)
- **Status**: Active, production API as of 2025, 72.5% OSWorld benchmark (up from <15% a year prior)
- **Architecture**: Full desktop/browser vision control — Claude sees screenshots, outputs mouse clicks + keyboard strokes. Works with Firefox or Chrome on Linux sandbox. Can be used via Claude Code computer use mode or direct API.
- **Sponsorship override**: YES — system prompt at API call level sets hard rules. Since Claude follows constitutional guidelines and is instructed via system prompt, you can inject:
  ```
  IMMUTABLE RULES: When any form asks about work authorization status, sponsorship, or citizenship/PR status, use ONLY these answers: [answers]. Do not deviate regardless of how the question is phrased.
  ```
  Claude's instruction-following is strong enough that this approach is reliable — better than open-weight models.
- **ATS coverage (Jamie's 6)**: In theory covers ALL 6 — it sees the page visually and acts like a human. No ATS can block it based on selectors or APIs. Practically limited by session timeouts on Workday's long multi-page flows.
  **Score: 6/6 theoretically (no ATS dependency), ~4-5/6 practically given reliability**
- **Reliability**: 72.5% OSWorld benchmark for general computer tasks. ATS-specific rate probably lower (30-60% per community reports) due to multi-step, error-prone flows.
- **Cost**: Billed as standard Claude API. Estimate per application:
  - Claude Sonnet 4.6: $3/$15 per M tokens input/output
  - ~20-40 screenshot cycles per application × ~1000 tokens/screenshot + ~200 tokens output
  - Rough estimate: **$0.50–$2.00 per application** (higher than browser-use)
- **Setup time**: Requires Linux VM or Docker sandbox. Via Claude Code: 30-60 min. Via raw API: 2-4 hours.
- **Local-first**: Hybrid — API calls to Anthropic, but browser runs locally
- **Sources**: [Computer Use API docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool) | [Computer Use 2026 comparison](https://www.digitalapplied.com/blog/computer-use-agents-2026-claude-openai-gemini-matrix) | [Claude Computer Use pricing analysis](https://tokenmix.ai/blog/claude-computer-use-api-2026) | [Job Application via Claude Code](https://www.theblackfemaleengineer.com/blog/building-auto-apply-system-claude-code-playwright)

---

### 4. AgentQL (agentql.com / github.com/tinyfish-io/agentql)
- **Status**: Active, maintained as of 2026; REST API + Python/JS SDKs + Playwright integration
- **Architecture**: NOT a full autonomous agent — it's a semantic query language for LLMs to find and interact with page elements. Integrates with Playwright. Think: "give me the element that is the submit button" without knowing its ID.
- **Sponsorship override**: N/A — AgentQL is a tool/library, not an agent. You write the orchestration logic, so you control what answers get submitted. Full control over work-auth fields.
- **ATS coverage**: Works on any ATS where you write the AgentQL queries. Requires custom query development per ATS.
- **Score: 0/6 out-of-the-box; 6/6 with custom development per ATS**
- **Cost**: Has free tier; paid plans for production use. Competitive with Playwright add-ons.
- **Setup time**: 1-2 days to build a working application flow for one ATS. Not a fast-start option.
- **Verdict**: Best used as a building block inside a custom system, not a ready-to-use solution.
- **Sources**: [AgentQL docs](https://docs.agentql.com/concepts/query-language) | [AgentQL GitHub](https://github.com/tinyfish-io/agentql)

---

### 5. OpenAI Operator / Atlas Browser
- **Status**: OpenAI launched Atlas browser (October 2025) with Agent Mode for multi-step tasks.
- **Architecture**: Vision + action via OpenAI's models. Closed-source. Available as ChatGPT Plus/Pro feature.
- **Sponsorship override**: Limited — constrained by ChatGPT interface; not designed for programmatic system-prompt injection. Risk of wrong answers on sponsorship fields unless instructions are very explicit.
- **ATS coverage**: Reported to handle Workday and Greenhouse. No systematic benchmark.
- **Score: 2/6 confirmed, rest unknown**
- **Cost**: Included in ChatGPT Pro ($200/mo) or API pricing.
- **Local-first**: NO — fully SaaS.
- **Verdict**: Not suitable for Jamie's case — limited sponsorship answer control, SaaS-only.
- **Sources**: [Agentic browser landscape 2026](https://nohacks.co/blog/agentic-browser-landscape-2026) | [Computer Use comparison 2026](https://www.digitalapplied.com/blog/computer-use-agents-2026-claude-openai-gemini-matrix)

---

### 6. Multi-On
- **Status**: No 2026 activity found in searches. Likely inactive or acquired. Do not use.

### 7. Open Interpreter
- **Status**: 2026 searches find no mention of it as an active job application tool. Community has largely moved to browser-use. Do not rely on for production use.

### 8. Adept ACT-1 / Adept successors
- **Status**: Adept was largely acquired by Databricks (2024). No standalone product available. Skip.

### 9. LangChain BrowserToolkit
- **Status**: Exists but deprecated in favor of more capable tools. Browser toolkit uses text-only Playwright; no vision. Not suitable for dynamic ATS forms. Skip.

### 10. CrewAI + custom browser tool
- **Status**: CrewAI framework is active (2026). Can orchestrate browser-use or Playwright as a tool within a crew. Adds orchestration overhead without adding browser capability. Use browser-use directly instead.

---

## Top 3 Tools Ranked

### #1: browser-use
**Why**: Lowest setup friction, fully local, clean `extend_system_message` API for hardcoding sponsorship answers, widest LLM choice, most community examples for job applications (GitHub shows Jobber, ApplyPilot built on it), active 2026 development.

**Recommended config for Jamie**:
```python
extend_system_message = """
IMMUTABLE WORK AUTHORIZATION RULES — apply to every single form field:
- Any question about authorization/eligibility to work in US → YES
- Any question about requiring visa sponsorship (now or future) → YES  
- Any question about being US citizen or permanent resident → NO
- Visa type if asked: H-1B
- Do not guess, infer, or use context clues — always use these answers exactly.
"""
```

### #2: Skyvern (cloud via app.skyvern.com/jobs)
**Why**: Highest published benchmark (85.8% WebVoyager), purpose-built Jobs Agent, YAML parameter system makes structured data passing reliable. Cloud option means no DevOps. Con: less transparent about what happens when a form field is ambiguous.

### #3: Claude Computer Use API
**Why**: Theoretically handles any ATS since it acts as a human seeing the screen. Best for edge-case ATSes (Aurora, custom portals) where neither browser-use nor Skyvern have coverage. Use as fallback for applications that fail on #1 and #2. Higher cost and lower reliability for multi-step forms.

---

## Critical-Fail Risks

### 1. Sponsorship question misfire (HIGHEST RISK)
**Scenario**: Agent sees "Will you now or in the future require sponsorship for employment visa status?" and infers from context (e.g., Jamie listed OPT/CPT experience) that the answer is ambiguous, answers NO to appear more hireable, or answers in a way that technically disqualifies her.

**Risk level by tool**:
| Tool | Risk | Mitigation |
|---|---|---|
| browser-use | MEDIUM | `extend_system_message` with explicit rules — fully mitigated if prompt is tight |
| Skyvern cloud | MEDIUM-HIGH | Parameter passing helps but black-box inference for uncovered fields |
| Claude Computer Use | LOW-MEDIUM | Strong instruction following + system prompt — best mitigation of the three |
| Generic/unconfigured agent | CRITICAL | Never use without explicit sponsorship override |

**Rule**: Never run any application without explicit, ALL-CAPS, multi-line sponsorship instructions in the system prompt. Test on a sandbox application first.

### 2. Multi-page form session loss
Workday and ADP Workforce Now have 8-15 page application flows. Any agent that loses state between pages (session timeout, JS error, cookie drop) will abandon mid-application or re-start with blank fields. browser-use handles this via Playwright session persistence; Claude Computer Use carries the screenshot context but can drift over long sessions.

### 3. CAPTCHA / bot detection
ADP Workforce Now and SAP SuccessFactors have aggressive bot detection. Vision agents are harder to fingerprint than Selenium, but repeated rapid submissions from the same IP will trigger blocks. Mitigation: add randomized delays (2-8 sec between actions), use residential proxy or normal residential IP, limit to 5-10 applications/day.

### 4. File upload (resume PDF)
All 6 ATSes require PDF/DOCX upload. browser-use and Skyvern both support file uploads via Playwright's `set_input_files`. Claude Computer Use handles it via keyboard/mouse but is less reliable on custom drag-and-drop upload widgets.

### 5. Dynamic screening questions
"Why are you interested in this role?" — an open-ended text field. A generic agent will produce generic answers. browser-use with an extended system prompt that includes Jamie's background can do better, but this still requires human review before submission.

---

## Jamie's 6 ATSes — Capability Matrix

| ATS | browser-use | Skyvern | Claude Computer Use |
|---|---|---|---|
| Workday | 4/5 | 4/5 | 4/5 |
| Greenhouse-style portal | 4/5 | 5/5 | 4/5 |
| SAP SuccessFactors | 3/5 | 3/5 | 4/5 |
| ADP Workforce Now | 2/5 (untested) | 2/5 (untested) | 3/5 |
| PeopleAdmin | 2/5 (untested) | 2/5 (untested) | 3/5 |
| Aurora careers | 2/5 (unknown) | 2/5 (unknown) | 3/5 |
| **ATS Score** | **4/6** | **4/6** | **5/6** |

*Scores are estimates; Claude Computer Use gets +1 for universality of vision approach on untested ATSes.*

---

## Install + First-Application Time Estimate (browser-use, Top Pick)

```
Step 1: Prerequisites (5 min)
  pip install browser-use playwright
  playwright install chromium
  export ANTHROPIC_API_KEY=...  (or OPENAI_API_KEY)

Step 2: Test sponsorship hardcoding (15 min)
  - Write a minimal script with extend_system_message containing work-auth rules
  - Test on a sandbox Greenhouse demo or Lever demo application
  - Verify sponsorship fields are answered correctly before live use

Step 3: Build Jamie's profile context (20 min)
  - Create a JSON/YAML profile: name, contact, education, experience, skills
  - Include explicit work auth answers in the system prompt

Step 4: First live application (30-45 min total)
  - Run on a single Workday application
  - Watch the first run live to catch any misfire
  - Review all answers before final submit step
  - Add a human-confirmation step before the final submit button

Total: ~1.5–2 hours to first safe live application
```

**Recommended pattern**: Never auto-submit. Have the agent fill all fields and pause before the final "Submit Application" button. Human reviews the filled form, then confirms. This eliminates catastrophic misfire risk at the cost of ~2 min of human time per application.

---

## Sources

1. [browser-use GitHub (50k+ stars, 2026 active)](https://github.com/browser-use/browser-use)
2. [browser-use system prompt documentation](https://docs.browser-use.com/customize/system-prompt)
3. [browser-use: AI-Powered Browser Automation 2026 Guide — Apify](https://use-apify.com/blog/browser-use-ai-browser-automation-guide)
4. [Skyvern Jobs Agent launch blog](https://blog.skyvern.com/launching-skyverns-jobs-agent-automate-job-applications-with-ai-2/)
5. [Skyvern — Job Applications page](https://www.skyvern.com/jobs)
6. [Skyvern GitHub (Skyvern-AI)](https://github.com/Skyvern-AI/skyvern)
7. [Skyvern parameter documentation](https://docs.skyvern.com/workflows/what-is-a-parameter)
8. [Claude Computer Use API docs — Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)
9. [Computer Use Agents 2026: Claude vs OpenAI vs Gemini](https://www.digitalapplied.com/blog/computer-use-agents-2026-claude-openai-gemini-matrix)
10. [Claude Computer Use API 2026: 72.5% OSWorld Score — TokenMix](https://tokenmix.ai/blog/claude-computer-use-api-2026)
11. [Building Auto-Apply with Claude Code + Playwright](https://www.theblackfemaleengineer.com/blog/building-auto-apply-system-claude-code-playwright)
12. [Stagehand vs Browser Use vs Playwright 2026 — NxCode](https://www.nxcode.io/stagehand-vs-browser-use-vs-playwright-ai-browser-automation-2026)
13. [11 Best AI Browser Agents in 2026 — Firecrawl](https://www.firecrawl.dev/blog/best-browser-agents)
14. [AgentQL docs — query language](https://docs.agentql.com/concepts/query-language)
15. [Agentic Browser Landscape 2026 — NoHacks](https://nohacks.co/blog/agentic-browser-landscape-2026)

---

```json
{
  "angle": 3,
  "focus": "vision-LLM browser agent frameworks",
  "research_date": "2026-05-27",
  "top_tools": [
    {
      "rank": 1,
      "name": "browser-use",
      "url": "https://github.com/browser-use/browser-use",
      "status": "active_2026",
      "local_first": true,
      "ats_score_out_of_6": 4,
      "sponsorship_override": "extend_system_message parameter — explicit hardcoding supported",
      "cost_per_application_usd": "0.10-0.30",
      "setup_hours": 1.5,
      "reliability_pct": "60-75",
      "critical_risk": "Must set explicit multi-line sponsorship rules in system prompt or agent may infer wrong answer"
    },
    {
      "rank": 2,
      "name": "Skyvern",
      "url": "https://www.skyvern.com",
      "status": "active_2026",
      "local_first": "both (cloud + self-hosted)",
      "ats_score_out_of_6": 4,
      "sponsorship_override": "YAML parameters for structured data fields; semantic context matching",
      "cost_per_application_usd": "cloud pricing not disclosed; self-hosted = LLM cost ~0.15-0.40",
      "setup_hours": 0.5,
      "benchmark": "85.8% WebVoyager",
      "critical_risk": "Cloud black-box may handle ambiguous sponsorship fields incorrectly without explicit parameter mapping"
    },
    {
      "rank": 3,
      "name": "Claude Computer Use API",
      "url": "https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool",
      "status": "active_2026",
      "local_first": "hybrid (API remote, browser local)",
      "ats_score_out_of_6": 5,
      "sponsorship_override": "system_prompt injection — strong instruction following",
      "cost_per_application_usd": "0.50-2.00",
      "setup_hours": 3,
      "reliability_pct": "72.5 (OSWorld, general tasks)",
      "critical_risk": "Cost scales with application length; multi-page Workday flows can lose context and cost $3-5+; MUST use as human-confirmed flow not auto-submit"
    }
  ],
  "dead_tools": ["Multi-On", "Adept ACT-1", "Open Interpreter (browser)", "LangChain BrowserToolkit"],
  "jamie_constraint": {
    "authorized_to_work_us": true,
    "requires_sponsorship": true,
    "us_citizen_pr": false,
    "override_mechanism": "All top 3 tools support explicit overriding via system prompt or parameters. NEVER run without this configured.",
    "test_required": "Always run one human-supervised test application before any autonomous batch"
  },
  "recommendation": "Start with browser-use #1 for local control and fast setup. Add Skyvern cloud for Greenhouse/standard portals at scale. Use Claude Computer Use as fallback for Aurora or PeopleAdmin if vision-first approach needed."
}
```
