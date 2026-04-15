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
    """Read from env vars first, then st.secrets (for Streamlit Community Cloud)."""
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
    """
    Create a managed agent session, send the company name,
    stream events, and return the brief as markdown text.
    Deletes the session when done to release resources.
    """
    client = Anthropic(api_key=config.api_key)

    prompt = (
        f'Research the company "{company_name}" and generate an Alkira '
        f"opportunity brief. Follow the brief structure and writing style in your "
        f"instructions exactly. Include the Alkira Fit Score, strategic sales "
        f"questions, and references. Focus on information from the past 12 months. "
        f"Return the brief as markdown text. Do not narrate your process."
    )

    status_callback("Starting agent session...", "init")
    session = client.beta.sessions.create(
        agent=config.agent_id,
        environment_id=config.env_id,
        title=f"Alkira Brief: {company_name}",
    )

    brief_parts: list[str] = []

    try:
        status_callback(f"Researching {company_name}...", "research")
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
                    raise TimeoutError(
                        f"Agent did not finish within {timeout_seconds / 60:.0f} minutes"
                    )

                if not hasattr(event, "type"):
                    continue

                if event.type == "agent.message":
                    for block in getattr(event, "content", []):
                        if getattr(block, "type", None) == "text":
                            brief_parts.append(block.text)

                if event.type == "agent.tool_use":
                    tool_name = getattr(event, "name", "")
                    if "search" in tool_name:
                        status_callback(
                            f"Searching the web for {company_name} intel...",
                            "search",
                        )
                    elif "skill" in tool_name or "read" in tool_name:
                        status_callback(
                            "Analyzing Alkira knowledge base...",
                            "analyze",
                        )

                if event.type == "session.status_idle":
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
    """Strip agent narration before the actual brief starts."""
    markers = [
        "# ALKIRA OPPORTUNITY BRIEF",
        "ALKIRA OPPORTUNITY BRIEF",
    ]
    for marker in markers:
        idx = raw.find(marker)
        if idx != -1:
            return raw[idx:]
    return raw


def extract_score(brief: str) -> tuple[int, str]:
    """Pull the fit score and reasoning from the brief. Returns (score, reasoning)."""
    match = re.search(
        r"\*?\*?Alkira Fit Score:\s*(\d)\s*/\s*5\*?\*?",
        brief,
    )
    score = int(match.group(1)) if match else 0

    reasoning = ""
    if match:
        after = brief[match.end():]
        after = after.lstrip("* \n")
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


def extract_section(brief: str, heading: str) -> str:
    """Extract content under a specific H3 heading."""
    pattern = rf"###?\s*{re.escape(heading)}\s*\n"
    match = re.search(pattern, brief, re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_heading = re.search(r"\n###?\s", brief[start:])
    end = start + next_heading.start() if next_heading else len(brief)
    return brief[start:end].strip()


# ── Custom CSS ───────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    .stDeployButton, #MainMenu, footer { display: none !important; visibility: hidden !important; }

    /* ── Hero ────────────────────────────────────── */
    .hero {
        background: linear-gradient(135deg, #0a1628 0%, #1a365d 50%, #234e7e 100%);
        border-radius: 16px;
        padding: 2rem 2rem 1.8rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: '';
        position: absolute;
        top: -40%;
        right: -15%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        color: #7dd3fc;
        font-size: 0.65rem;
        font-weight: 600;
        padding: 0.2rem 0.55rem;
        border-radius: 20px;
        margin-bottom: 0.6rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .hero h2 {
        font-size: 1.6rem;
        font-weight: 800;
        color: #fff;
        margin: 0 0 0.3rem;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .hero p {
        font-size: 0.88rem;
        color: rgba(255,255,255,0.6);
        margin: 0;
        line-height: 1.45;
        max-width: 500px;
    }

    /* ── Buttons ──────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1a365d 0%, #2563eb 100%);
        color: white !important;
        border: none;
        padding: 0.65rem 1.5rem;
        font-size: 0.88rem;
        font-weight: 600;
        border-radius: 10px;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
        transform: translateY(-1px);
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #065f46 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.25) !important;
    }

    /* ── Status ───────────────────────────────────── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
        padding: 0.55rem 1rem;
        border-radius: 10px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 0.4rem 0;
        width: 100%;
    }
    .status-dot {
        width: 7px; height: 7px;
        background: #0ea5e9;
        border-radius: 50%;
        animation: pulse 1.4s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.75); }
    }

    /* ── Score card ───────────────────────────────── */
    .score-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .score-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 0 0 0.4rem;
    }
    .score-stars {
        font-size: 1.6rem;
        letter-spacing: 2px;
        margin: 0 0 0.4rem;
        line-height: 1;
    }
    .score-reason {
        font-size: 0.82rem;
        color: #475569;
        line-height: 1.5;
        margin: 0;
    }
    .star-filled { color: #f59e0b; }
    .star-empty { color: #e2e8f0; }

    /* ── Brief container ──────────────────────────── */
    .brief-wrap {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 2rem 2.25rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        line-height: 1.65;
        color: #1e293b;
    }
    .brief-wrap h1 {
        font-size: 1.3rem;
        font-weight: 800;
        color: #0f172a;
        border-bottom: 2px solid #1a365d;
        padding-bottom: 0.5rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.01em;
    }
    .brief-wrap h2 {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1a365d;
        margin-top: 0.4rem;
        margin-bottom: 0.3rem;
    }
    .brief-wrap h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e40af;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .brief-wrap p {
        font-size: 0.87rem;
        margin-bottom: 0.6rem;
    }
    .brief-wrap ul, .brief-wrap ol {
        font-size: 0.87rem;
        padding-left: 1.2rem;
        margin-bottom: 0.7rem;
    }
    .brief-wrap li {
        margin-bottom: 0.35rem;
        line-height: 1.55;
    }
    .brief-wrap strong { color: #0f172a; }
    .brief-wrap em { color: #64748b; }
    .brief-wrap a {
        color: #2563eb;
        text-decoration: none;
        border-bottom: 1px solid #93c5fd;
    }
    .brief-wrap a:hover { border-bottom-color: #2563eb; }
    .brief-wrap table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
        margin: 0.6rem 0;
    }
    .brief-wrap th {
        background: #f1f5f9;
        padding: 0.5rem 0.75rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
    }
    .brief-wrap td {
        padding: 0.4rem 0.75rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .brief-wrap hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 1.25rem 0;
    }
    .brief-wrap blockquote {
        border-left: 3px solid #2563eb;
        padding-left: 1rem;
        color: #475569;
        margin: 0.6rem 0;
    }

    /* ── Sidebar ──────────────────────────────────── */
    [data-testid="stSidebar"] { background: #f8fafc; }
    .sidebar-title {
        font-size: 0.7rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.75rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #e2e8f0;
    }

    /* ── Tab styling ──────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #f1f5f9;
        border-radius: 10px;
        padding: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background: #fff !important;
        color: #1a365d !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* ── Meta bar ─────────────────────────────────── */
    .meta-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .meta-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .meta-time {
        font-size: 0.7rem;
        color: #94a3b8;
    }
</style>
"""


# ── Render helpers ───────────────────────────────────────────────

def render_score_card(score: int, reasoning: str) -> None:
    """Render the Alkira Fit Score as a visual card."""
    filled = "".join(
        f'<span class="star-filled">&#9733;</span>' for _ in range(score)
    )
    empty = "".join(
        f'<span class="star-empty">&#9733;</span>' for _ in range(5 - score)
    )

    color_map = {5: "#059669", 4: "#0d9488", 3: "#64748b", 2: "#94a3b8", 1: "#cbd5e1"}
    border_color = color_map.get(score, "#94a3b8")

    st.markdown(
        f'<div class="score-card" style="border-left: 4px solid {border_color};">'
        f'<p class="score-label">Alkira Fit Score</p>'
        f'<p class="score-stars">{filled}{empty}</p>'
        f'<p class="score-reason">{reasoning}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_brief(brief_md: str) -> None:
    """Render the brief markdown inside a styled container."""
    st.markdown(
        f'<div class="brief-wrap">{_md_to_html_simple(brief_md)}</div>',
        unsafe_allow_html=True,
    )


def _md_to_html_simple(md: str) -> str:
    """Minimal markdown to HTML for rendering inside styled container.
    Streamlit's st.markdown handles most things, but we need raw HTML
    inside our div, so we do a lightweight conversion."""
    import html as html_lib

    lines = md.split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        # Close open lists if needed
        if in_ul and not stripped.startswith("- ") and not stripped.startswith("* "):
            out.append("</ul>")
            in_ul = False
        if in_ol and not re.match(r"^\d+\.\s", stripped):
            out.append("</ol>")
            in_ol = False

        # Blank line
        if not stripped:
            out.append("")
            continue

        # Headings
        if stripped.startswith("# "):
            out.append(f"<h1>{_inline(stripped[2:])}</h1>")
            continue
        if stripped.startswith("## "):
            out.append(f"<h2>{_inline(stripped[3:])}</h2>")
            continue
        if stripped.startswith("### "):
            out.append(f"<h3>{_inline(stripped[4:])}</h3>")
            continue

        # Horizontal rule
        if stripped in ("---", "***", "___"):
            out.append("<hr/>")
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            content = stripped[2:]
            out.append(f"<li>{_inline(content)}</li>")
            continue

        # Ordered list
        ol_match = re.match(r"^(\d+)\.\s(.+)", stripped)
        if ol_match:
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_inline(ol_match.group(2))}</li>")
            continue

        # Regular paragraph
        out.append(f"<p>{_inline(stripped)}</p>")

    # Close any open lists
    if in_ul:
        out.append("</ul>")
    if in_ol:
        out.append("</ol>")

    return "\n".join(out)


def _inline(text: str) -> str:
    """Convert inline markdown (bold, italic, links, code) to HTML."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Links
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
        st.markdown(
            '<p class="sidebar-title">Brief History</p>',
            unsafe_allow_html=True,
        )
        if not st.session_state.brief_history:
            st.caption("No briefs generated yet.")
        else:
            for i, entry in enumerate(st.session_state.brief_history):
                score = entry.get("score", 0)
                stars = ("&#9733;" * score) + ("&#9734;" * (5 - score))
                with st.expander(
                    f"{entry['company']}  |  {entry.get('time', '')}",
                    expanded=False,
                ):
                    st.markdown(
                        f"<span style='color:#f59e0b;font-size:0.9rem;'>{stars}</span>",
                        unsafe_allow_html=True,
                    )
                    st.download_button(
                        label="Download",
                        data=entry["brief_md"],
                        file_name=f"{entry['company'].replace(' ', '_')}_Alkira_Brief.md",
                        mime="text/markdown",
                        key=f"sb_{i}",
                    )

        st.markdown("---")
        st.caption("Powered by Alkira + Claude")

    # ── Hero ─────────────────────────────────────────────────
    st.markdown(
        '<div class="hero">'
        '<div class="hero-badge">Channel Sales Intelligence</div>'
        "<h2>Alkira Opportunity Brief Generator</h2>"
        "<p>Enter a company name. The agent researches it and builds a "
        "scored opportunity brief with Alkira fit analysis, proof points, "
        "and strategic sales questions.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Config check ─────────────────────────────────────────
    config = load_config()
    if not config.agent_id or not config.env_id or not config.api_key:
        st.error(
            "Missing configuration. Set `ANTHROPIC_API_KEY`, `ALKIRA_AGENT_ID`, "
            "and `ALKIRA_ENV_ID` in `.env` or Streamlit secrets."
        )
        return

    # ── Input ────────────────────────────────────────────────
    col1, col2 = st.columns([4, 1])
    with col1:
        company_name = st.text_input(
            "Company name",
            placeholder="e.g.  Mary Kay,  Chevron,  Walmart,  Koch Industries",
            label_visibility="collapsed",
        )
    with col2:
        generate = st.button("Generate", use_container_width=True)

    # ── Generation ───────────────────────────────────────────
    if generate and company_name.strip():
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        phase_pct = {"init": 5, "research": 20, "search": 45, "analyze": 75}
        step = {"n": 0}

        def update_status(msg: str, phase: str = "research") -> None:
            step["n"] += 1
            pct = phase_pct.get(phase, min(step["n"] * 12, 90))
            progress_bar.progress(min(pct, 95))
            status_placeholder.markdown(
                f'<div class="status-pill">'
                f'<span class="status-dot"></span>{msg}'
                f"</div>",
                unsafe_allow_html=True,
            )

        start = time.time()

        try:
            with st.spinner(""):
                raw = run_agent_session(
                    config, company_name.strip(), update_status,
                )

            elapsed = time.time() - start
            progress_bar.progress(100)
            status_placeholder.empty()
            progress_bar.empty()

            # Clean and parse
            brief_md = clean_brief(raw)
            score, reasoning = extract_score(brief_md)

            # ── Meta bar ─────────────────────────────────
            st.markdown(
                f'<div class="meta-bar">'
                f'<span class="meta-label">Opportunity Brief</span>'
                f'<span class="meta-time">Generated in {elapsed:.0f}s</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Score + download row ─────────────────────
            sc_col, dl_col = st.columns([3, 1])
            with sc_col:
                render_score_card(score, reasoning)
            with dl_col:
                safe = company_name.strip().replace(" ", "_")
                st.download_button(
                    label="Download Brief",
                    data=brief_md,
                    file_name=f"{safe}_Alkira_Brief.md",
                    mime="text/markdown",
                    key="main_dl",
                )

            # ── Tabbed brief display ─────────────────────
            tab_full, tab_sales, tab_refs = st.tabs([
                "Full Brief", "Sales Playbook", "References",
            ])

            with tab_full:
                render_brief(brief_md)

            with tab_sales:
                sales_q = extract_section(brief_md, "Strategic Sales Questions")
                entry_pts = extract_section(brief_md, "Partner Entry Points")
                why_now = extract_section(brief_md, "Why Now")

                if entry_pts:
                    st.markdown("#### Partner Entry Points")
                    st.markdown(entry_pts)
                if why_now:
                    st.markdown("#### Why Now")
                    st.markdown(why_now)
                if sales_q:
                    st.markdown("#### Strategic Sales Questions")
                    st.markdown(sales_q)

                if not (sales_q or entry_pts or why_now):
                    st.info("Sales sections not found in brief output.")

            with tab_refs:
                refs = extract_section(brief_md, "References")
                confidence = extract_section(brief_md, "Confidence & Gaps")

                if confidence:
                    st.markdown("#### Confidence & Gaps")
                    st.markdown(confidence)
                if refs:
                    st.markdown("#### Sources")
                    st.markdown(refs)

                if not (refs or confidence):
                    st.info("Reference sections not found in brief output.")

            # ── Save to history ──────────────────────────
            timestamp = time.strftime("%I:%M %p")
            st.session_state.brief_history.insert(0, {
                "company": company_name.strip(),
                "brief_md": brief_md,
                "score": score,
                "time": timestamp,
            })
            st.session_state.brief_history = st.session_state.brief_history[:10]

        except TimeoutError:
            progress_bar.empty()
            status_placeholder.empty()
            st.error("Timed out after 5 minutes. Try again.")

        except Exception as exc:
            progress_bar.empty()
            status_placeholder.empty()
            st.error(f"Something went wrong: {exc}")

    elif generate:
        st.warning("Enter a company name first.")

    # ── Footer ───────────────────────────────────────────────
    with st.expander("How it works"):
        st.markdown(
            "1. **Enter a company name** you or a partner is pursuing.\n"
            "2. **The agent researches it** across the web for cloud strategy, "
            "IT leadership, M&A activity, and pain signals.\n"
            "3. **Alkira fit is scored 1-5 stars** based on evidence strength.\n"
            "4. **You get a brief** with proof points, sales questions tied to "
            "real data, and verifiable source references.\n\n"
            "Briefs typically take 2-4 minutes."
        )


if __name__ == "__main__":
    main()
