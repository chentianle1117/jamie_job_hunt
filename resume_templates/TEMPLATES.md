# Resume Templates

Clean, non-tailored HTML resumes with role-appropriate bullet variants pre-selected.
**Never edit these directly.** Copy to `tailored_resumes/` first, then tailor.

## How to Start a New Application

1. Pick the template closest to the role type
2. Copy it: `cp resume_templates/template_EX-WX.html tailored_resumes/CompanyName_RoleType_YYYY-MM-DD.html`
3. Open in Claude and run `/tailor` — add diff UI (toolbar, change-log, highlights) during tailoring
4. Export PDF: headless Chrome → `tailored_resumes/CompanyName_RoleType_YYYY-MM-DD.pdf`
5. When ready to apply, copy PDF to resume_bank

## Available Templates

| File | Role Type | InGenius Variant | Use When JD Mentions |
|------|-----------|-----------------|----------------------|
| `template_base.html` | General / Default | L&D/Ops | General HR/OD — no clear emphasis |
| `template_EX-WX.html` | Employee/Workplace Experience | Engagement/HR | "employee experience", "workplace", "culture", "people programs" |
| `template_PM.html` | Program Management | PM emphasis | "program management", "operations", "project lifecycle", "cross-functional" |
| `template_LD.html` | Learning & Development | L&D/Ops | "learning design", "curriculum", "instructional", "L&D", "enablement" |
| `template_HR-HRBP.html` | HR / HRBP | Vendor/PM | "HRBP", "HR generalist", "HR business partner", "talent", "ER" |

## What Changes Per Template

| | Base | EX-WX | PM | L&D | HR-HRBP |
|---|---|---|---|---|---|
| Summary | OD professional | OD & Workplace Experience | OD & Program Mgmt | OD & Learning Design | HR & OD |
| InGenius title | Program Enablement Manager | Program Enablement Manager | Program Management Specialist | Program Enablement Manager | Program Enablement Manager |
| InGenius bullets | L&D/Ops | Engagement/HR | PM emphasis | L&D/Ops | Vendor/PM |
| Vestas order | Default (DEI first) | EX first (culture/wellbeing) | Default | Default | HRBP framing |
| NextGen order | Default | EX analysis first | Default | L&D framing | Default |
| Skills emphasis | Standard | Google Workspace, Notion | Airtable, Notion | LMS heavy | HRIS heavy |
| Location | Portland/Remote/Seattle | Open to relocation | Portland/Remote/Seattle | Portland/Remote/Seattle | Portland/Remote/Seattle |
