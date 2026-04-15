"""
Alkira Opportunity Brief Generator — Web App

Streamlit frontend for the Managed Agent. Partners type a company name,
the agent researches it and returns a formatted brief on the page.

Usage:
    streamlit run app.py
"""

import os
import re
import time
from dataclasses import dataclass

import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ── Configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class AgentConfig:
    agent_id: str
    env_id: str
    api_key: str


def _secret(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        try:
            val = st.secrets.get(key, "")
        except FileNotFoundError:
            pass
    return val


def load_config() -> AgentConfig:
    return AgentConfig(
        agent_id=_secret("ALKIRA_AGENT_ID"),
        env_id=_secret("ALKIRA_ENV_ID"),
        api_key=_secret("ANTHROPIC_API_KEY"),
    )


# ── Agent Session ────────────────────────────────────────────────

def run_agent_session(
    config: AgentConfig,
    company_name: str,
    status_callback,
    timeout_seconds: float = 300,
) -> str:
    client = Anthropic(api_key=config.api_key)

    prompt = (
        f'Research the company "{company_name}" and generate an Alkira '
        f"opportunity brief. Follow the brief structure and writing style in your "
        f"instructions exactly. Include the Alkira Fit Score, strategic sales "
        f"questions, and references. Focus on information from the past 12 months. "
        f"Return the brief as markdown text. Do not narrate your process."
    )

    status_callback("init")
    session = client.beta.sessions.create(
        agent=config.agent_id,
        environment_id=config.env_id,
        title=f"Alkira Brief: {company_name}",
    )

    brief_parts: list[str] = []

    try:
        status_callback("research")
        session_start = time.monotonic()

        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": prompt}],
                    },
                ],
            )

            for event in stream:
                if time.monotonic() - session_start > timeout_seconds:
                    raise TimeoutError("Agent did not finish in time")

                if not hasattr(event, "type"):
                    continue

                if event.type == "agent.message":
                    for block in getattr(event, "content", []):
                        if getattr(block, "type", None) == "text":
                            brief_parts.append(block.text)

                if event.type == "agent.tool_use":
                    tool_name = getattr(event, "name", "")
                    if "search" in tool_name:
                        status_callback("search")
                    elif "skill" in tool_name or "read" in tool_name:
                        status_callback("analyze")

                if event.type == "session.status_idle":
                    status_callback("done")
                    break

                if event.type == "session.error":
                    msg = getattr(
                        getattr(event, "error", None), "message", "unknown"
                    )
                    brief_parts.append(f"\n\n[Error: {msg}]")
                    break

        return "".join(brief_parts)

    finally:
        try:
            client.beta.sessions.delete(session.id)
        except Exception:
            pass


# ── Brief Parsing ────────────────────────────────────────────────

def clean_brief(raw: str) -> str:
    markers = ["# ALKIRA OPPORTUNITY BRIEF", "ALKIRA OPPORTUNITY BRIEF"]
    for marker in markers:
        idx = raw.find(marker)
        if idx != -1:
            return raw[idx:]
    return raw


def extract_score(brief: str) -> tuple[int, str]:
    match = re.search(r"\*?\*?Alkira Fit Score:\s*(\d)\s*/\s*5\*?\*?", brief)
    score = int(match.group(1)) if match else 0
    reasoning = ""
    if match:
        after = brief[match.end():].lstrip("* \n")
        lines = after.split("\n")
        reason_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if reason_lines:
                    break
                continue
            if stripped.startswith("#") or stripped.startswith("---"):
                break
            reason_lines.append(stripped)
        reasoning = " ".join(reason_lines)
    return score, reasoning


def extract_company_header(brief: str) -> tuple[str, str]:
    """Extract company name and stats line from the brief."""
    lines = brief.split("\n")
    company = ""
    stats = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") and "OPPORTUNITY" not in stripped.upper():
            company = stripped.lstrip("# ").strip()
            continue
        if company and stripped.startswith("**") and (
            "HQ" in stripped or "Revenue" in stripped or "Industry" in stripped
        ):
            stats = stripped
            break
    return company, stats


def extract_section(brief: str, heading: str) -> str:
    pattern = rf"###?\s*{re.escape(heading)}\s*\n"
    match = re.search(pattern, brief, re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n###?\s", brief[start:])
    end = start + next_heading.start() if next_heading else len(brief)
    return brief[start:end].strip()


def get_brief_body(brief: str) -> str:
    """Get the brief content starting from Executive Summary onward,
    excluding the title, company header, and score (rendered separately)."""
    markers = [
        "### Executive Summary",
        "## Executive Summary",
        "### Infrastructure Snapshot",
        "### Company Snapshot",
        "### Cloud & Infrastructure",
    ]
    for marker in markers:
        idx = brief.find(marker)
        if idx != -1:
            # Find the CONFIDENTIAL marker or end
            end_markers = ["*CONFIDENTIAL*", "*\"CONFIDENTIAL\"*", "CONFIDENTIAL"]
            end_idx = len(brief)
            for em in end_markers:
                ei = brief.find(em, idx)
                if ei != -1:
                    end_idx = min(end_idx, ei + len(em))
            return brief[idx:end_idx].strip()
    return brief


# ── HTML Rendering ───────────────────────────────────────────────

def md_to_html(md: str) -> str:
    """Convert brief markdown to styled HTML."""
    lines = md.split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        if in_ul and not stripped.startswith("- ") and not stripped.startswith("* "):
            out.append("</ul>")
            in_ul = False
        if in_ol and not re.match(r"^\d+\.\s", stripped):
            out.append("</ol>")
            in_ol = False

        if not stripped:
            continue

        # Section headings get special treatment
        if stripped.startswith("### "):
            title = stripped[4:]
            out.append(
                f'<div class="section-head">'
                f'<div class="section-accent"></div>'
                f'<h3>{inline(title)}</h3>'
                f'</div>'
            )
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("# "):
            continue  # Skip H1, rendered separately

        if stripped in ("---", "***", "___"):
            continue  # Skip HRs, we use section borders

        if stripped.startswith("- ") or stripped.startswith("* "):
            content = stripped[2:]
            # Detect sub-heading bullets like "**Confidence level:** ..." or "**What we know (confirmed):**"
            sub_match = re.match(r"\*\*(.+?):?\*\*:?\s*(.*)", content)
            if sub_match and len(sub_match.group(1)) > 8 and (
                sub_match.group(1)[0].isupper()
            ):
                # Close any open list before the sub-heading
                if in_ul:
                    out.append("</ul>")
                    in_ul = False
                label = sub_match.group(1).rstrip(":")
                rest = sub_match.group(2).strip()
                out.append(
                    f'<div class="sub-heading">'
                    f'<span class="sub-label">{label}</span>'
                )
                if rest:
                    out.append(f'<span class="sub-inline">{inline(rest)}</span>')
                out.append("</div>")
                continue
            if not in_ul:
                out.append('<ul class="brief-list">')
                in_ul = True
            out.append(f"<li>{inline(content)}</li>")
            continue

        ol_match = re.match(r"^(\d+)\.\s(.+)", stripped)
        if ol_match:
            if not in_ol:
                out.append('<ol class="brief-list">')
                in_ol = True
            out.append(f"<li>{inline(ol_match.group(2))}</li>")
            continue

        # CONFIDENTIAL footer
        if "CONFIDENTIAL" in stripped.upper():
            out.append(
                '<p class="confidential">CONFIDENTIAL</p>'
            )
            continue

        out.append(f"<p>{inline(stripped)}</p>")

    if in_ul:
        out.append("</ul>")
    if in_ol:
        out.append("</ol>")

    return "\n".join(out)


def inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[(\d+)\]\s*(.+?)\s*[—–-]\s*(https?://\S+)",
        r'<a href="\3" target="_blank">[\1] \2</a>',
        text,
    )
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        r'<a href="\2" target="_blank">\1</a>',
        text,
    )
    return text


# ── Custom CSS ───────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ── Reset & Global ──────────────────────────── */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #f4f6f9;
    }
    .stDeployButton, #MainMenu, footer,
    header[data-testid="stHeader"] { display: none !important; }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 820px !important;
    }

    /* ── Hero ────────────────────────────────────── */
    .hero {
        background: linear-gradient(140deg, #0b1a33 0%, #152a4e 40%, #1e3f6e 100%);
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.25rem;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '';
        position: absolute;
        top: -60%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(59,130,246,0.07) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-top {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .hero-icon {
        width: 28px;
        height: 28px;
        background: rgba(59,130,246,0.2);
        border-radius: 7px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
    }
    .hero-badge {
        font-size: 0.6rem;
        font-weight: 700;
        color: #93c5fd;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .hero h2 {
        font-size: 1.35rem;
        font-weight: 800;
        color: #fff;
        margin: 0 0 0.25rem;
        letter-spacing: -0.02em;
    }
    .hero p {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.5);
        margin: 0;
        line-height: 1.45;
    }

    /* ── Search bar ──────────────────────────────── */
    .search-wrap {
        background: #fff;
        border: 1px solid #dde3eb;
        border-radius: 12px;
        padding: 0.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    div[data-testid="stTextInput"] > div > div > input {
        border: none !important;
        box-shadow: none !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 0.8rem !important;
        background: transparent !important;
    }
    div[data-testid="stTextInput"] > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ── Buttons ──────────────────────────────────── */
    .stButton > button {
        background: #1a3a6b;
        color: white !important;
        border: none;
        padding: 0.6rem 1.6rem;
        font-size: 0.82rem;
        font-weight: 700;
        border-radius: 9px;
        width: 100%;
        transition: all 0.15s ease;
        letter-spacing: 0.01em;
    }
    .stButton > button:hover {
        background: #244d8a;
        box-shadow: 0 3px 10px rgba(26,58,107,0.25);
    }
    .stDownloadButton > button {
        background: #fff !important;
        color: #1a3a6b !important;
        border: 1.5px solid #dde3eb !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        border-radius: 8px !important;
        padding: 0.45rem 1rem !important;
    }
    .stDownloadButton > button:hover {
        background: #f4f6f9 !important;
        border-color: #1a3a6b !important;
    }

    /* ── Step tracker ─────────────────────────────── */
    .step-tracker {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        padding: 1.25rem 0;
        margin: 0.5rem 0;
    }
    .step {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .step-dot {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.65rem;
        font-weight: 700;
        flex-shrink: 0;
        transition: all 0.3s ease;
    }
    .step-dot.pending {
        background: #e8ecf1;
        color: #94a3b8;
    }
    .step-dot.active {
        background: #1a3a6b;
        color: #fff;
        box-shadow: 0 0 0 4px rgba(26,58,107,0.15);
        animation: step-pulse 1.5s ease-in-out infinite;
    }
    .step-dot.done {
        background: #059669;
        color: #fff;
    }
    .step-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: #94a3b8;
        transition: color 0.3s ease;
    }
    .step-label.active { color: #1a3a6b; }
    .step-label.done { color: #059669; }
    .step-line {
        width: 36px;
        height: 2px;
        background: #e8ecf1;
        margin: 0 0.35rem;
        flex-shrink: 0;
        transition: background 0.3s ease;
    }
    .step-line.done { background: #059669; }
    @keyframes step-pulse {
        0%, 100% { box-shadow: 0 0 0 4px rgba(26,58,107,0.15); }
        50% { box-shadow: 0 0 0 8px rgba(26,58,107,0.08); }
    }

    /* ── Results card ─────────────────────────────── */
    .result-card {
        background: #fff;
        border: 1px solid #dde3eb;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .result-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.6rem;
    }
    .result-company {
        font-size: 1.2rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .result-meta {
        font-size: 0.72rem;
        color: #94a3b8;
    }
    .result-stats {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-top: 0.5rem;
    }
    .stat-pill {
        display: inline-block;
        background: #f4f6f9;
        color: #475569;
        font-size: 0.67rem;
        font-weight: 500;
        padding: 0.2rem 0.55rem;
        border-radius: 5px;
    }
    .score-row {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid #f1f5f9;
    }
    .score-stars {
        font-size: 1.15rem;
        letter-spacing: 1px;
        line-height: 1;
    }
    .star-on { color: #f59e0b; }
    .star-off { color: #e2e8f0; }
    .score-num {
        font-size: 0.75rem;
        font-weight: 700;
        color: #475569;
    }
    .score-reason {
        font-size: 0.75rem;
        color: #64748b;
        line-height: 1.45;
        margin-top: 0.4rem;
    }

    /* ── Tabs ─────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: #edf0f4;
        border-radius: 10px;
        padding: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.45rem 1rem;
        border-radius: 8px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background: #fff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* ── Brief document ──────────────────────────── */
    .brief-doc {
        background: #fff;
        border: 1px solid #dde3eb;
        border-radius: 14px;
        padding: 1.8rem 2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        color: #1e293b;
        line-height: 1.6;
    }
    .brief-doc h2 {
        font-size: 1rem;
        font-weight: 700;
        color: #152a4e;
        margin: 1.2rem 0 0.4rem;
    }
    .brief-doc .section-head {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 1.6rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid #edf0f4;
    }
    .brief-doc .section-accent {
        width: 3px;
        height: 18px;
        background: #2563eb;
        border-radius: 2px;
        flex-shrink: 0;
    }
    .brief-doc .section-head h3 {
        font-size: 0.82rem;
        font-weight: 700;
        color: #1a3a6b;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .brief-doc p {
        font-size: 0.82rem;
        margin-bottom: 0.5rem;
    }
    .brief-doc .brief-list {
        font-size: 0.82rem;
        padding-left: 1.1rem;
        margin: 0.3rem 0 0.6rem;
    }
    .brief-doc .brief-list li {
        margin-bottom: 0.3rem;
        line-height: 1.5;
    }
    .brief-doc .brief-list li::marker {
        color: #2563eb;
    }
    .brief-doc strong { color: #0f172a; }
    .brief-doc em { color: #64748b; font-style: italic; }
    .brief-doc a {
        color: #2563eb;
        text-decoration: none;
    }
    .brief-doc a:hover { text-decoration: underline; }
    .brief-doc code {
        background: #f1f5f9;
        padding: 0.1rem 0.3rem;
        border-radius: 3px;
        font-size: 0.78rem;
    }
    .brief-doc .sub-heading {
        margin-top: 0.9rem;
        margin-bottom: 0.25rem;
        padding: 0.45rem 0.65rem;
        background: #f4f6f9;
        border-radius: 6px;
        border-left: 3px solid #cbd5e1;
    }
    .brief-doc .sub-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #334155;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        display: block;
    }
    .brief-doc .sub-inline {
        font-size: 0.78rem;
        color: #475569;
        display: block;
        margin-top: 0.15rem;
        line-height: 1.45;
    }
    .brief-doc .confidential {
        text-align: center;
        font-size: 0.7rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #edf0f4;
    }

    /* ── Sidebar ──────────────────────────────────── */
    [data-testid="stSidebar"] { background: #f9fafb; }
    [data-testid="stSidebar"] .block-container { padding-top: 1.5rem !important; }
    .sb-title {
        font-size: 0.65rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.6rem;
    }
    .sb-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0.6rem;
        border-radius: 8px;
        margin-bottom: 0.25rem;
        transition: background 0.1s ease;
        cursor: default;
    }
    .sb-item:hover { background: #f1f5f9; }
    .sb-company {
        font-size: 0.78rem;
        font-weight: 600;
        color: #1e293b;
    }
    .sb-right {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .sb-stars {
        font-size: 0.7rem;
        color: #f59e0b;
        letter-spacing: 0.5px;
    }
    .sb-time {
        font-size: 0.62rem;
        color: #94a3b8;
    }

    /* ── How it works ─────────────────────────────── */
    .hiw-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.6rem;
        margin: 0.5rem 0;
    }
    .hiw-card {
        background: #f4f6f9;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
    .hiw-num {
        width: 22px;
        height: 22px;
        background: #1a3a6b;
        color: #fff;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .hiw-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0;
    }
    .hiw-desc {
        font-size: 0.62rem;
        color: #64748b;
        margin: 0.15rem 0 0;
        line-height: 1.35;
    }
</style>
"""


# ── Step tracker ─────────────────────────────────────────────────

STEPS = [
    ("1", "Starting"),
    ("2", "Researching"),
    ("3", "Analyzing"),
    ("4", "Composing"),
]

PHASE_TO_STEP = {
    "init": 0,
    "research": 1,
    "search": 1,
    "analyze": 2,
    "compose": 3,
    "done": 4,
}


def render_step_tracker(current_phase: str) -> str:
    active_idx = PHASE_TO_STEP.get(current_phase, 0)
    parts = []
    for i, (num, label) in enumerate(STEPS):
        if i < active_idx:
            dot_cls = "done"
            label_cls = "done"
            icon = "&#10003;"
        elif i == active_idx:
            dot_cls = "active"
            label_cls = "active"
            icon = num
        else:
            dot_cls = "pending"
            label_cls = ""
            icon = num

        parts.append(
            f'<div class="step">'
            f'<span class="step-dot {dot_cls}">{icon}</span>'
            f'<span class="step-label {label_cls}">{label}</span>'
            f'</div>'
        )
        if i < len(STEPS) - 1:
            line_cls = "done" if i < active_idx else ""
            parts.append(f'<div class="step-line {line_cls}"></div>')

    return f'<div class="step-tracker">{"".join(parts)}</div>'


# ── Streamlit UI ─────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Alkira Brief Generator",
        page_icon="https://alkira.com/favicon.ico",
        layout="centered",
    )

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if "brief_history" not in st.session_state:
        st.session_state.brief_history = []

    # ── Sidebar ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown('<p class="sb-title">History</p>', unsafe_allow_html=True)

        if not st.session_state.brief_history:
            st.caption("No briefs yet.")
        else:
            for i, entry in enumerate(st.session_state.brief_history):
                s = entry.get("score", 0)
                stars_html = "&#9733;" * s + "&#9734;" * (5 - s)
                st.markdown(
                    f'<div class="sb-item">'
                    f'<span class="sb-company">{entry["company"]}</span>'
                    f'<div class="sb-right">'
                    f'<span class="sb-stars">{stars_html}</span>'
                    f'<span class="sb-time">{entry.get("time", "")}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    label=f"Download",
                    data=entry["brief_md"],
                    file_name=f"{entry['company'].replace(' ', '_')}_Brief.md",
                    mime="text/markdown",
                    key=f"sb_{i}",
                )

    # ── Hero ─────────────────────────────────────────────────
    st.markdown(
        '<div class="hero">'
        '<div class="hero-top">'
        '<div class="hero-icon">&#9670;</div>'
        '<span class="hero-badge">Channel Sales Intelligence</span>'
        '</div>'
        "<h2>Alkira Brief Generator</h2>"
        "<p>Research any company. Get a scored opportunity brief with "
        "Alkira fit analysis, proof points, and sales questions.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Config ───────────────────────────────────────────────
    config = load_config()
    if not config.agent_id or not config.env_id or not config.api_key:
        st.error(
            "Missing config. Set ANTHROPIC_API_KEY, ALKIRA_AGENT_ID, "
            "and ALKIRA_ENV_ID in .env or Streamlit secrets."
        )
        return

    # ── Search bar ───────────────────────────────────────────
    with st.form("brief_form", clear_on_submit=False, border=False):
        col1, col2 = st.columns([5, 1])
        with col1:
            company_name = st.text_input(
                "Company",
                placeholder="Enter a company name...",
                label_visibility="collapsed",
            )
        with col2:
            generate = st.form_submit_button("Generate", use_container_width=True)

    # ── Generation ───────────────────────────────────────────
    if generate and company_name.strip():
        tracker_ph = st.empty()
        current_phase = {"value": "init"}

        def update_status(phase: str) -> None:
            current_phase["value"] = phase
            tracker_ph.markdown(
                render_step_tracker(phase),
                unsafe_allow_html=True,
            )

        start = time.time()

        try:
            with st.spinner(""):
                raw = run_agent_session(
                    config, company_name.strip(), update_status,
                )

            elapsed = time.time() - start
            tracker_ph.empty()

            brief_md = clean_brief(raw)
            score, reasoning = extract_score(brief_md)
            company, stats_line = extract_company_header(brief_md)
            if not company:
                company = company_name.strip()

            # Parse stats into pills
            stat_pills = ""
            if stats_line:
                parts = re.split(r"\s*\|\s*", stats_line.strip("* "))
                pills = "".join(
                    f'<span class="stat-pill">{p.strip()}</span>'
                    for p in parts if p.strip()
                )
                stat_pills = f'<div class="result-stats">{pills}</div>'

            # Score stars
            filled = ''.join(
                '<span class="star-on">&#9733;</span>' for _ in range(score)
            )
            empty = ''.join(
                '<span class="star-off">&#9733;</span>' for _ in range(5 - score)
            )

            # ── Results card ─────────────────────────────
            st.markdown(
                f'<div class="result-card">'
                f'<div class="result-top">'
                f'<div>'
                f'<p class="result-company">{company}</p>'
                f'{stat_pills}'
                f'</div>'
                f'<span class="result-meta">Generated in {elapsed:.0f}s</span>'
                f'</div>'
                f'<div class="score-row">'
                f'<span class="score-stars">{filled}{empty}</span>'
                f'<span class="score-num">{score}/5</span>'
                f'</div>'
                f'<p class="score-reason">{reasoning}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Download ─────────────────────────────────
            safe = company_name.strip().replace(" ", "_")
            st.download_button(
                label=f"Download {company} Brief",
                data=brief_md,
                file_name=f"{safe}_Alkira_Brief.md",
                mime="text/markdown",
                key="main_dl",
            )

            # ── Tabs ─────────────────────────────────────
            tab_brief, tab_sales, tab_refs = st.tabs([
                "Brief", "Sales Playbook", "References",
            ])

            with tab_brief:
                body = get_brief_body(brief_md)
                html = md_to_html(body)
                st.markdown(
                    f'<div class="brief-doc">{html}</div>',
                    unsafe_allow_html=True,
                )

            with tab_sales:
                playbook = extract_section(brief_md, "Partner Playbook")
                signals = extract_section(brief_md, "Signals & Timing")
                if not playbook:
                    playbook = extract_section(brief_md, "Strategic Sales Questions")
                if not signals:
                    signals = extract_section(brief_md, "Why Now")

                content = ""
                if signals:
                    content += f"### Signals & Timing\n\n{signals}\n\n"
                if playbook:
                    content += f"### Partner Playbook\n\n{playbook}\n\n"

                if content:
                    html = md_to_html(content)
                    st.markdown(
                        f'<div class="brief-doc">{html}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("Sales sections not found.")

            with tab_refs:
                refs = extract_section(brief_md, "References")
                confidence = extract_section(brief_md, "Confidence & Gaps")
                content = ""
                if confidence:
                    content += f"### Confidence & Gaps\n\n{confidence}\n\n"
                if refs:
                    content += f"### References\n\n{refs}\n\n"

                if content:
                    html = md_to_html(content)
                    st.markdown(
                        f'<div class="brief-doc">{html}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("Reference sections not found.")

            # ── History ──────────────────────────────────
            timestamp = time.strftime("%I:%M %p")
            st.session_state.brief_history.insert(0, {
                "company": company,
                "brief_md": brief_md,
                "score": score,
                "time": timestamp,
            })
            st.session_state.brief_history = st.session_state.brief_history[:10]

        except TimeoutError:
            tracker_ph.empty()
            st.error("Timed out after 5 minutes. Try again.")

        except Exception as exc:
            tracker_ph.empty()
            st.error(f"Something went wrong: {exc}")

    elif generate:
        st.warning("Enter a company name first.")

    # ── How it works ─────────────────────────────────────────
    with st.expander("How it works"):
        st.markdown(
            '<div class="hiw-grid">'
            '<div class="hiw-card"><div class="hiw-num">1</div>'
            '<p class="hiw-label">Enter</p>'
            '<p class="hiw-desc">Type any company name</p></div>'
            '<div class="hiw-card"><div class="hiw-num">2</div>'
            '<p class="hiw-label">Research</p>'
            '<p class="hiw-desc">Agent searches the web</p></div>'
            '<div class="hiw-card"><div class="hiw-num">3</div>'
            '<p class="hiw-label">Score</p>'
            '<p class="hiw-desc">Maps to Alkira fit 1-5</p></div>'
            '<div class="hiw-card"><div class="hiw-num">4</div>'
            '<p class="hiw-label">Brief</p>'
            '<p class="hiw-desc">Proof points + questions</p></div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption("Briefs take 2-4 minutes.")


if __name__ == "__main__":
    main()
