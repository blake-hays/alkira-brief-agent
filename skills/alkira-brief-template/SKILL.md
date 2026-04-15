---
name: alkira-brief-template
description: "Brief template, scoring rubric, and output format for the Alkira Opportunity Brief Generator. Load this skill before composing any brief. Contains the 13-section brief structure with word limits, 1-5 star Alkira fit scoring criteria, strategic sales question format, research checklist, and confidence & gaps framework."
---

# Alkira Opportunity Brief — Template & Scoring

Load this skill before composing a brief. It defines what you're building: the output structure, scoring rubric, research targets, and quality expectations.

**CRITICAL: Brevity is a feature.** The entire brief must be under 1,500 words (excluding references). Each section has a max word count. A partner reads this between meetings. Dense beats thorough.

---

## Research Checklist

Find all of the following. Mark each finding as **(confirmed)** or **(directional)** in the brief.

| Category | What to find |
|----------|-------------|
| **Company basics** | HQ, revenue, employee count, industry, public/private |
| **Global footprint** | Offices, distribution centers, manufacturing, markets served |
| **IT leadership** | CIO/CTO name + background + recent quotes. Roles only if names not public. |
| **Cloud platforms** | All known or inferred providers (AWS, Azure, GCP). Classify by production, dev/test, specialised. |
| **On-prem / hybrid** | Name platforms if public: VMware, Nutanix, Citrix, HCI, etc. |
| **Network / security** | MPLS, multicloud, firewalls, SD-WAN, zero trust mentions |
| **Digital transformation** | Cloud migration, modernization, tech investments, AI initiatives |
| **Organisational signals** | Leadership changes, modernisation programmes, geographic expansion |
| **Pain signals** | Outages, security incidents, compliance pressure, cost-cutting, vendor consolidation |
| **Recent news** | M&A, expansion, funding, restructuring (past 12 months) |

---

## Alkira Fit Score (1-5 Stars)

Format:

```
**Alkira Fit Score: [X] / 5**
```

Then 2 sentences explaining why. Not 3. Two.

### Scoring Criteria

**5 Stars** — Strong fit, clear urgency
- Multiple entry points with direct evidence (active multicloud migration, MPLS expiring, M&A, stated cloud cost concerns)
- IT leadership publicly discussing infrastructure modernization
- Visible pain signals or budget triggers

**4 Stars** — Good fit, solid indicators
- 2+ strong entry points with evidence
- Cloud-forward but pain points inferred, not stated
- IT leadership identified but no public infra quotes

**3 Stars** — Moderate fit, worth pursuing
- 1-2 entry points with reasonable evidence
- Limited IT leadership visibility in public sources

**2 Stars** — Weak fit, needs discovery
- Entry points speculative based on size/industry
- Little public info on IT infrastructure

**1 Star** — Poor fit on available data
- No clear entry points; minimal cloud presence

---

## Brief Structure (13 Sections)

**Total target: under 1,500 words** (excluding references). Section limits below are maximums, not targets. Shorter is better.

### 1. Title
H1: **"ALKIRA OPPORTUNITY BRIEF"** with date. *(5 words)*

### 2. Company Header
H2: **Company name** + stats line (HQ, revenue, employees, industry, markets, ownership). *(1 line)*

### 3. Alkira Fit Score
Score + 2-sentence rationale. *(~50 words max)*

### 4. Executive Summary *(~100 words max)*
H3: **"Executive Summary"** — 4-6 bullet points that stand alone. Each bullet is 1 sentence. Cover: fit assessment, scale/regulatory gravity, primary complexity source. A partner reads ONLY this and decides whether to pursue.

### 5. Cloud & Infrastructure Reality *(~120 words max)*
H3: **"Cloud & Infrastructure Reality"** — Single consolidated view:
- **Cloud Platforms**: Provider list with (confirmed)/(directional) tags
- **On-Prem / Hybrid**: Named platforms if public
- **Deployment Model**: 1 sentence with evidence
- **Resulting Complexity**: 2 sentences max. Plain English.

### 6. Organisational & Strategic Signals *(~80 words max)*
H3: **"Organisational & Strategic Signals"** — Max 4 bullets, 1-2 sentences each. Only signals that affect networking decisions. Name concrete examples.

### 7. Three Areas Where Alkira Fits *(~300 words max, ~100 per entry point)*
H3: **"Three Areas Where Alkira Fits"** — For each of 3 entry points, bold subheading, then:
- **Why it matters here**: 1-2 sentences. The signal from research.
- **How Alkira solves it**: 1-2 sentences. The capability.
- **Proof point**: 1 sentence. Real metric from alkira-customer skill.

Keep each entry point tight. No multi-paragraph explanations.

### 8. Partner Entry Points *(~80 words max)*
H3: **"Partner Entry Points"**:
- **Likely stakeholders**: 3-5 role titles on one line
- **Opening angle**: 1-2 sentences
- **Validate early**: 3-4 short bullet points

### 9. Why Now *(~60 words max)*
H3: **"Why Now"** — 3-4 bullet points, 1 sentence each.

### 10. Strategic Sales Questions *(~200 words max)*
H3: **"Strategic Sales Questions"** — Exactly 5 numbered questions.

Each question: 1-2 sentences max. Must reference a specific data point from research. Include a short parenthetical on the angle it opens.

Example:
```
1. "Your CEO mentioned a 25% IT cost reduction target. Where does 
   networking sit in that?" *(TCO angle — Alkira saves 40-60%)*
```

Keep questions conversational and tight. No multi-sentence setups.

### 11. Confidence & Gaps *(~120 words max)*
H3: **"Confidence & Gaps"**:
- **Confidence**: High/Medium/Low + 1 sentence
- **Confirmed**: 3-5 bullet points (short)
- **Directional**: 2-4 bullet points (short)
- **Uncertainties**: 2-3 bullet points
- **Discovery questions**: 2-3 questions

### 12. References
H3: **"References"** — Numbered list. Format: `[N] Description — URL`. No word limit but keep descriptions short (5-8 words each).

### 13. Confidentiality
*"CONFIDENTIAL"*

---

## Quality Gate

Before delivering the brief, verify:

- [ ] Total word count under 1,500 (excluding references)
- [ ] No section exceeds its word limit
- [ ] Every bullet is 1-2 sentences max
- [ ] Every company claim has (confirmed) or (directional) label
- [ ] Proof points come from alkira-customer skill metrics
- [ ] Sales questions reference specific research data
- [ ] No AI writing patterns (load stop-slop skill for checks)
- [ ] No em dashes anywhere
- [ ] No adverbs
- [ ] No filler phrases or throat-clearing
