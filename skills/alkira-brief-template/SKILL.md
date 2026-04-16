---
name: alkira-brief-template
description: "Brief template, scoring rubric, and output format for the Alkira Opportunity Brief Generator. Load this skill before composing any brief. Contains the brief structure with strict sentence limits, 1-5 star scoring criteria, and research checklist."
---

# Alkira Opportunity Brief — Template & Scoring

Load this skill before composing a brief.

**THE BRIEF MUST FIT ON TWO PRINTED PAGES.** That means ~700 words of content (excluding references). Every section below has a sentence limit. Do not exceed it. If you write a sentence that doesn't add new information, delete it.

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

Then **3-4 sentences** explaining why. This is the most important paragraph in the brief. A partner reads this and decides whether to pursue. Cover: the strongest evidence for Alkira fit, the primary complexity source, and what holds the score back (if anything). Be specific — reference actual findings from research.

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
Score line + 3-4 sentence rationale. See above. This replaces the executive summary — make it count.

### 4. Infrastructure Snapshot — MAX 8 SENTENCES TOTAL
Single consolidated section. Cover:
- Cloud platforms with (confirmed)/(directional) tags — 1-2 sentences
- On-prem/hybrid platforms — 1 sentence
- Deployment model — 1 sentence
- What this means for connectivity and governance — 2 sentences max

### 5. Signals & Timing — MAX 4 BULLETS, 1 SENTENCE EACH
Only signals that create urgency or affect networking decisions. Each bullet is 1 sentence.

### 6. Three Alkira Entry Points — MAX 3 SENTENCES PER ENTRY POINT
For each of the 3 entry points, bold subheading, then exactly 3 sentences:
1. **Signal**: What you found in research that supports this. (1 sentence)
2. **Solution**: How Alkira addresses it. (1 sentence)
3. **Proof**: One metric from the alkira-customer skill. (1 sentence)

That's 9 sentences total for this section. Not 12. Not 15. Nine.

### 7. Conversation Starters

This is the most actionable section. It's written for **partner sales reps who are NOT network engineers**. They need questions they can ask comfortably in a business meeting without sounding like they're running a technical audit.

**Stakeholders:** 3-5 role titles on one line.

**5 Questions:** Each question must follow these rules:

1. **Use plain business language.** No technical jargon. No mention of "segmentation," "east-west traffic," "VPC," "policy enforcement," or "network architecture." If a non-technical sales rep would hesitate to say it out loud, rewrite it.

2. **Reference a specific fact about the company.** A name, a number, an event, an acquisition, a quote. This shows the rep did their homework.

3. **Sound like a curious human, not an auditor.** The question should feel like something you'd ask over coffee. "How's that going?" beats "What is your current approach to managing..."

4. **Keep it to one sentence.** Short sentences are easier to memorize and say naturally.

5. **Include a parenthetical that explains:** (a) what the question is really trying to uncover, and (b) what the Alkira angle is if the answer confirms the pain. Write this for the rep — it's their cheat sheet for what to listen for.

**Example of GOOD questions:**
```
1. "How's the Jetro integration going on the IT side?" 
   *(You're listening for: timeline pressure, overlapping systems, manual work. If it's painful, Alkira cuts partner onboarding time by 98%.)*

2. "Your CIO said stitching clouds together is hard — is that getting better or worse?"
   *(You're listening for: frustration with multi-cloud complexity. Alkira connects clouds in a single click with 96% faster connection time.)*

3. "With four new distribution centers opening this year, how does a new site get connected?"
   *(You're listening for: slow provisioning, circuit lead times, manual config. Alkira deploys connectivity 80% faster with no hardware.)*
```

**Example of BAD questions (do NOT write these):**
- "How are you managing network policy and segmentation across both environments today?" *(Too technical — rep won't ask this)*
- "What does cross-cloud connectivity look like for your SAGE platform?" *(Assumes knowledge of Alkira's value prop)*
- "Is network infrastructure in scope on the CIO's roadmap alongside application migration?" *(Sounds like a consultant, not a human)*

**Validate early:** 2-3 bullets. Plain language. What the rep should try to confirm in the first conversation. Example: "Find out if they're still paying for old MPLS lines" not "Determine the current WAN architecture composition."

### 8. References
Numbered list. Format: `[N] Description — URL`. Short descriptions.

### 9. Confidentiality
```
*CONFIDENTIAL*
```

---

## Quality Gate

Before delivering:

- [ ] Total brief fits on ~2 printed pages (~700 words excluding references)
- [ ] Fit score rationale is 3-4 sentences and answers "should I pursue this?"
- [ ] No section exceeds its sentence limit
- [ ] Each Alkira entry point is exactly 3 sentences
- [ ] Sales questions use plain business language — no networking jargon
- [ ] A non-technical sales rep could read every question out loud comfortably
- [ ] Every claim labeled (confirmed) or (directional)
- [ ] No AI writing patterns (check stop-slop skill)
- [ ] No em dashes, no adverbs, no filler
- [ ] No "Executive Summary" section (the fit score rationale serves this purpose)
- [ ] No "Confidence & Gaps" section (confirmed/directional labels handle this inline)
