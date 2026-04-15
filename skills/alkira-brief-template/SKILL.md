---
name: alkira-brief-template
description: "Brief template, scoring rubric, and output format for the Alkira Opportunity Brief Generator. Load this skill before composing any brief. Contains the brief structure with strict sentence limits, 1-5 star scoring criteria, and research checklist."
---

# Alkira Opportunity Brief — Template & Scoring

Load this skill before composing a brief.

**THE BRIEF MUST FIT ON TWO PRINTED PAGES.** That means ~800 words of content (excluding references). Every section below has a sentence limit. Do not exceed it. If you write a sentence that doesn't add new information, delete it.

---

## Research Checklist

Find all of the following. Mark findings as **(confirmed)** or **(directional)**.

| Category | What to find |
|----------|-------------|
| Company basics | HQ, revenue, employees, industry, public/private |
| Global footprint | Offices, facilities, markets served |
| IT leadership | CIO/CTO name + background. Roles only if names not public. |
| Cloud platforms | Providers (AWS, Azure, GCP). Production vs dev/test. |
| On-prem / hybrid | VMware, Nutanix, Citrix, HCI if public |
| Network / security | MPLS, multicloud, firewalls, SD-WAN, zero trust |
| Organisational signals | Leadership changes, M&A, expansion, cost-cutting |
| Pain signals | Outages, compliance pressure, vendor consolidation |

---

## Alkira Fit Score (1-5 Stars)

```
**Alkira Fit Score: [X] / 5**
```

Then **exactly 2 sentences** explaining why. Not 3.

**5** — Multiple entry points with direct evidence. Active infrastructure modernization.
**4** — 2+ entry points with evidence. Cloud-forward but pain inferred, not stated.
**3** — 1-2 entry points with reasonable evidence. Limited public detail.
**2** — Entry points speculative. Little public infrastructure info.
**1** — No clear entry points on available data.

---

## Brief Structure

**Sentence limits are hard limits. Do not exceed them.**

### 1. Title
```
# ALKIRA OPPORTUNITY BRIEF
*[Month Year]*
```

### 2. Company Header
```
## [Company Name]
**HQ:** X | **Revenue:** X | **Employees:** X | **Industry:** X | **Markets:** X | **Ownership:** X
```
One line. No paragraph.

### 3. Fit Score
Score line + 2 sentences. See above.

### 4. Executive Summary — MAX 5 BULLETS, 1 SENTENCE EACH
Each bullet is one sentence. No bullet exceeds 25 words. A partner reads only this and decides whether to pursue. Cover: fit assessment, scale, primary complexity source.

### 5. Infrastructure Snapshot — MAX 8 SENTENCES TOTAL
Single consolidated section. Cover:
- Cloud platforms with (confirmed)/(directional) tags — 1-2 sentences
- On-prem/hybrid platforms — 1 sentence
- Deployment model — 1 sentence
- What this means for connectivity and governance — 2 sentences max

### 6. Signals & Timing — MAX 4 BULLETS, 1 SENTENCE EACH
Combines organisational signals and timing triggers into one section. Only signals that create urgency or affect networking decisions. Each bullet is 1 sentence.

### 7. Three Alkira Entry Points — MAX 3 SENTENCES PER ENTRY POINT
For each of the 3 entry points, bold subheading, then exactly 3 sentences:
1. **Signal**: What you found in research that supports this. (1 sentence)
2. **Solution**: How Alkira addresses it. (1 sentence)
3. **Proof**: One metric from the alkira-customer skill. (1 sentence)

That's 9 sentences total for this section. Not 12. Not 15. Nine.

### 8. Partner Playbook — MAX 12 SENTENCES TOTAL
Combines entry points, sales questions, and discovery into one actionable section:

**Stakeholders:** 3-5 role titles on one line.
**Opening angle:** 1 sentence.

**5 Sales Questions:** Each question is 1 sentence with a short parenthetical angle note. No multi-sentence setups. Example:
```
1. "Your IT director said legacy customization made it hard to move fast — is that still true for the network layer?" *(Opens infra modernization conversation)*
```

**Validate early:** 3 bullets, 1 sentence each.

### 9. Confidence & Gaps — MAX 6 SENTENCES
- Confidence: High/Medium/Low + 1 sentence why.
- 2-3 key unknowns as a comma-separated list in 1 sentence.
- 2 discovery questions in 2 sentences.

This section is 4-6 sentences. Not a full page. Be blunt.

### 10. References
Numbered list. Format: `[N] Description — URL`. Short descriptions.

### 11. Confidentiality
```
*CONFIDENTIAL*
```

---

## Quality Gate

Before delivering:

- [ ] Total brief fits on ~2 printed pages (~800 words excluding references)
- [ ] Executive Summary bullets are 1 sentence each
- [ ] No section exceeds its sentence limit
- [ ] Each Alkira entry point is exactly 3 sentences
- [ ] Sales questions are 1 sentence each
- [ ] Confidence & Gaps is under 6 sentences
- [ ] Every claim labeled (confirmed) or (directional)
- [ ] No AI writing patterns (check stop-slop skill)
- [ ] No em dashes, no adverbs, no filler
