---
name: alkira-brief-template
description: "Brief template, scoring rubric, and output format for the Alkira Opportunity Brief Generator. Load this skill before composing any brief. Contains the 13-section brief structure, 1-5 star Alkira fit scoring criteria, strategic sales question format, research checklist, and confidence & gaps framework."
---

# Alkira Opportunity Brief — Template & Scoring

Load this skill before composing a brief. It defines what you're building: the output structure, scoring rubric, research targets, and quality expectations.

---

## Research Checklist

When researching a company, find all of the following. Mark each finding as **(confirmed)** or **(directional)** in the brief.

| Category | What to find |
|----------|-------------|
| **Company basics** | HQ, revenue, employee count, industry, public/private |
| **Global footprint** | Offices, distribution centers, manufacturing, markets served |
| **IT leadership** | CIO/CTO name + background + recent quotes. Use roles only if names are not public. |
| **Cloud platforms** | All known or inferred providers (AWS, Azure, GCP, others). Classify by production, dev/test, or specialised workloads. |
| **On-prem / hybrid** | Name specific platforms if public: VMware, Nutanix, Citrix, HCI, etc. |
| **Network / security** | MPLS, multicloud connectivity, firewalls, SD-WAN, zero trust, network transformation mentions |
| **Digital transformation** | Cloud migration, infrastructure modernization, tech investments, AI initiatives |
| **Organisational signals** | Leadership changes, operating model shifts, modernisation programmes, geographic or ecosystem expansion |
| **Pain signals** | Outages, security incidents, compliance pressure, cost-cutting, vendor consolidation |
| **Recent news** | M&A, expansion, funding, restructuring (focus on past 12 months) |

---

## Alkira Fit Score (1-5 Stars)

Place the score prominently near the top of the brief after the company stats line:

```
**Alkira Fit Score: [X] / 5**
```

Then 2-3 sentences explaining why.

### Scoring Criteria

**5 Stars** — Strong fit with clear urgency
- Multiple Alkira entry points supported by direct evidence (e.g., active multicloud migration, MPLS contract expiring, M&A activity, stated cloud cost concerns)
- IT leadership publicly discussing infrastructure modernization
- Recent budget or initiative signals (cloud investment announcements, digital transformation programs)
- Pain signals visible (outages, complexity complaints, vendor consolidation efforts)

**4 Stars** — Good fit with solid indicators
- At least 2 strong entry points with evidence
- Company is clearly cloud-forward but specific pain points are inferred rather than stated
- IT leadership identified but no recent public quotes on infrastructure priorities
- Industry peers are adopting similar solutions

**3 Stars** — Moderate fit, worth pursuing
- 1-2 entry points with reasonable evidence
- Company uses cloud but infrastructure modernization isn't a stated priority
- Limited IT leadership visibility in public sources
- General industry trends suggest relevance

**2 Stars** — Weak fit, requires more discovery
- Entry points are speculative based on company size/industry rather than direct evidence
- Little public information on IT infrastructure or cloud strategy
- No visible pain signals or timing triggers
- May be too small or too early in cloud journey

**1 Star** — Poor fit based on available data
- No clear entry points based on research
- Company appears to have minimal cloud presence or doesn't align with Alkira's value proposition
- Insufficient information to build a credible brief (note this clearly)

---

## Brief Structure (13 Sections)

Return markdown with exactly this structure:

### 1. Title
H1: **"ALKIRA OPPORTUNITY BRIEF"** with date on the next line.

### 2. Company Header
H2: **Company name**, with key stats on the next line (HQ, revenue, employees, industry, markets, public/private).

### 3. Alkira Fit Score
Score line and reasoning. See scoring criteria above.

### 4. Executive Summary
H3: **"Executive Summary"** — 4-6 bullet points that stand alone. Cover:
- Overall Alkira fit assessment
- Enterprise scale or regulatory gravity (if applicable)
- Primary source of hybrid/multi-cloud complexity

A partner should be able to read ONLY this section and know whether to pursue.

### 5. Cloud & Infrastructure Reality
H3: **"Cloud & Infrastructure Reality"** — A single consolidated view:

- **Cloud Platforms**: List all known or inferred providers. For each, note confirmed vs directional and workload type. Example: "Azure (confirmed, primary production), AWS (directional, likely dev/test)"
- **On-Prem / Hybrid**: Name specific platforms if public (VMware, Nutanix, etc.)
- **Deployment Model**: On-prem, hybrid, or multi-cloud with evidence
- **Resulting Complexity**: 2-3 sentences in plain English describing what this means for connectivity, governance, and operational risk

### 6. Organisational & Strategic Signals
H3: **"Organisational & Strategic Signals"** — Max 5 bullet points. Only signals that materially affect cloud networking decisions: leadership changes, modernisation programmes, geographic expansion, M&A, cost restructuring. Name at least one concrete example if public.

### 7. Three Areas Where Alkira Fits
H3: **"Three Areas Where Alkira Fits"** — For each of the 3 entry points, use a bold subheading (e.g. **1. Multi-Cloud Networking**) followed by:

- **Why it matters here**: What signal from the research supports this
- **How Alkira solves it**: Specific capability mapped to their situation
- **Proof point**: Real Alkira metric from the alkira-customer skill

### 8. Partner Entry Points
H3: **"Partner Entry Points"**:

- **Likely stakeholders**: 3-5 roles (not names unless publicly confirmed). Example: "VP Infrastructure, Cloud Architect, CISO"
- **Best first conversation angle**: 1-2 sentences on how to open
- **What must be validated early**: 3-4 bullet points on unknowns the partner should confirm in discovery

### 9. Why Now
H3: **"Why Now"** — 3-4 bullet points on timing triggers.

### 10. Strategic Sales Questions
H3: **"Strategic Sales Questions"** — Exactly 5 numbered questions. Each must:

- Reference a specific data point from the research (a revenue target, a cloud migration, a cost-cutting initiative, an M&A deal)
- Be framed as a conversation opener to create urgency or uncover pain
- Include a parenthetical note on why this question matters or what angle it opens

Example:
```
1. "Your CEO mentioned targeting 25% reduction in IT spend this year. How is networking 
   infrastructure factoring into that goal?" 
   *(Opens door to TCO conversation — Alkira's 40-60% savings vs. traditional networking)*
```

Questions must sound like a real person, not a survey. Conversational tone. Generic questions like "What are your cloud plans?" are not acceptable.

### 11. Confidence & Gaps
H3: **"Confidence & Gaps"**:

- **Confidence level**: High / Medium / Low with 1 sentence explaining why
- **What we know (confirmed)**: 3-5 bullet points of verified facts
- **What we infer (directional)**: 2-4 bullet points of reasonable inferences with basis
- **Key uncertainties**: 2-3 things that could change the assessment
- **Recommended discovery questions**: 2-3 questions the partner should ask to fill gaps

This section is mandatory. Never skip it. Honesty builds partner trust.

### 12. References
H3: **"References"** — Numbered list of every source URL used during research. Format: `[N] Title or description — URL`. Include actual URLs so the reader can verify claims.

### 13. Confidentiality
*Italic: "CONFIDENTIAL"*
