"""
Alkira Opportunity Brief Generator — Web App

Streamlit frontend for the Managed Agent. Partners type a company name,
the agent researches it and returns a formatted brief on the page.

Usage:
    streamlit run app.py
"""

import os
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
        f"Return the brief as markdown text."
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


# ── Custom CSS ───────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
    /* ── Global ────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Hero section ──────────────────────────────── */
    .hero-container {
        background: linear-gradient(135deg, #0a1628 0%, #1a365d 50%, #234e7e 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: rgba(255, 255, 255, 0.65);
        margin: 0;
        line-height: 1.5;
        max-width: 520px;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.15);
        color: #7dd3fc;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    /* ── Input area ────────────────────────────────── */
    .input-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .input-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* ── Buttons ───────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #1a365d 0%, #2563eb 100%);
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        font-size: 0.9rem;
        font-weight: 600;
        border-radius: 10px;
        width: 100%;
        transition: all 0.2s ease;
        letter-spacing: 0.01em;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transform: translateY(-1px);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* ── Download button override ──────────────────── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #065f46 0%, #059669 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #047857 0%, #10b981 100%);
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);
    }

    /* ── Status indicator ──────────────────────────── */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        color: #0369a1;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.5rem 0;
        width: 100%;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background: #0ea5e9;
        border-radius: 50%;
        animation: pulse-dot 1.5s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    /* ── Brief card ────────────────────────────────── */
    .brief-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .brief-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .brief-header-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .brief-time {
        font-size: 0.75rem;
        color: #94a3b8;
    }

    /* ── Sidebar ───────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #f8fafc;
    }
    .sidebar-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .history-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .history-item:hover {
        border-color: #93c5fd;
        box-shadow: 0 1px 4px rgba(37, 99, 235, 0.1);
    }
    .history-company {
        font-size: 0.85rem;
        font-weight: 600;
        color: #1e293b;
        margin: 0;
    }
    .history-meta {
        font-size: 0.7rem;
        color: #94a3b8;
        margin: 0.15rem 0 0 0;
    }

    /* ── How-it-works ──────────────────────────────── */
    .how-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
    }
    .how-step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        background: #1a365d;
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        border-radius: 50%;
        margin-right: 0.6rem;
        flex-shrink: 0;
    }
    .how-step {
        display: flex;
        align-items: flex-start;
        margin-bottom: 0.6rem;
    }
    .how-step-text {
        font-size: 0.85rem;
        color: #334155;
        line-height: 1.5;
    }
    .how-step-text strong {
        color: #1e293b;
    }

    /* ── Config error ──────────────────────────────── */
    .config-error {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 1.25rem;
        color: #991b1b;
    }
    .config-error code {
        background: #fee2e2;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }

    /* ── Score badge ───────────────────────────────── */
    .score-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
    }

    /* ── Hide default streamlit elements for cleaner look ── */
    .stDeployButton { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* ── Expander tweaks ──────────────────────────── */
    .streamlit-expanderHeader {
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
"""


# ── Streamlit UI ─────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Alkira Brief Generator",
        page_icon="https://alkira.com/favicon.ico",
        layout="centered",
    )

    # Inject CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Session state ────────────────────────────────────────
    if "brief_history" not in st.session_state:
        st.session_state.brief_history = []

    # ── Sidebar: history ─────────────────────────────────────
    with st.sidebar:
        st.markdown('<p class="sidebar-title">Brief History</p>', unsafe_allow_html=True)

        if not st.session_state.brief_history:
            st.caption("No briefs generated yet.")
        else:
            for i, entry in enumerate(st.session_state.brief_history):
                with st.expander(f"{entry['company']}", expanded=False):
                    st.caption(f"Generated {entry.get('time', '')}")
                    st.markdown(entry["brief_md"][:500] + "...")
                    st.download_button(
                        label="Download Full Brief",
                        data=entry["brief_md"],
                        file_name=f"{entry['company'].replace(' ', '_')}_Alkira_Brief.md",
                        mime="text/markdown",
                        key=f"sidebar_dl_{i}",
                    )

        st.markdown("---")
        st.markdown(
            '<p style="font-size:0.7rem;color:#94a3b8;text-align:center;">'
            "Powered by Alkira + Claude"
            "</p>",
            unsafe_allow_html=True,
        )

    # ── Hero ─────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-badge">Channel Sales Intelligence</div>
            <p class="hero-title">Alkira Opportunity Brief Generator</p>
            <p class="hero-subtitle">
                Enter a company name. The agent researches it and builds a
                scored opportunity brief with Alkira fit analysis, proof points,
                and strategic sales questions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Config check ─────────────────────────────────────────
    config = load_config()
    if not config.agent_id or not config.env_id or not config.api_key:
        st.markdown(
            '<div class="config-error">'
            "<strong>Missing configuration.</strong> "
            "Make sure <code>.env</code> contains "
            "<code>ANTHROPIC_API_KEY</code>, <code>ALKIRA_AGENT_ID</code>, "
            "and <code>ALKIRA_ENV_ID</code>. "
            "Run <code>python setup_agent.py</code> first."
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Input ────────────────────────────────────────────────
    st.markdown(
        '<div class="input-card">'
        '<p class="input-label">Target Company</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([4, 1])
    with col1:
        company_name = st.text_input(
            "Company name",
            placeholder="e.g.  Mary Kay,  Chevron,  Walmart,  Koch Industries",
            label_visibility="collapsed",
        )
    with col2:
        generate = st.button("Generate Brief", use_container_width=True)

    # ── Generation ───────────────────────────────────────────
    if generate and company_name.strip():
        status_placeholder = st.empty()
        progress_bar = st.progress(0)

        step = {"count": 0}
        phase_progress = {
            "init": 5,
            "research": 15,
            "search": 40,
            "analyze": 70,
        }

        def update_status(msg: str, phase: str = "research") -> None:
            step["count"] += 1
            pct = phase_progress.get(phase, min(step["count"] * 10, 90))
            progress_bar.progress(min(pct, 95))
            status_placeholder.markdown(
                f'<div class="status-pill">'
                f'<span class="status-dot"></span>'
                f"{msg}"
                f"</div>",
                unsafe_allow_html=True,
            )

        start = time.time()

        try:
            with st.spinner(""):
                brief_md = run_agent_session(
                    config, company_name.strip(), update_status,
                )

            elapsed = time.time() - start
            progress_bar.progress(100)
            status_placeholder.empty()
            progress_bar.empty()

            # ── Success header ───────────────────────────────
            st.markdown(
                f'<div class="brief-header-bar">'
                f'<span class="brief-header-label">'
                f"Opportunity Brief"
                f"</span>"
                f'<span class="brief-time">'
                f"Generated in {elapsed:.0f}s"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── Download button ──────────────────────────────
            safe_name = company_name.strip().replace(" ", "_")
            st.download_button(
                label=f"Download {company_name.strip()} Brief",
                data=brief_md,
                file_name=f"{safe_name}_Alkira_Brief.md",
                mime="text/markdown",
                key="main_download",
            )

            # ── Brief content ────────────────────────────────
            st.markdown(brief_md)

            # ── Save to history ──────────────────────────────
            timestamp = time.strftime("%I:%M %p")
            st.session_state.brief_history.insert(0, {
                "company": company_name.strip(),
                "brief_md": brief_md,
                "time": timestamp,
            })
            st.session_state.brief_history = st.session_state.brief_history[:10]

        except TimeoutError:
            progress_bar.empty()
            status_placeholder.empty()
            st.error("Generation timed out after 5 minutes. Please try again.")

        except Exception as exc:
            progress_bar.empty()
            status_placeholder.empty()
            st.error(f"Something went wrong: {exc}")

    elif generate:
        st.warning("Enter a company name first.")

    # ── How it works ─────────────────────────────────────────
    st.markdown("")
    with st.expander("How it works"):
        steps = [
            (
                "Enter a company name",
                "Any company you or your partner is pursuing.",
            ),
            (
                "The agent researches it",
                "Searches the web for recent news, IT leadership, cloud strategy, "
                "network infrastructure, M&A activity, and pain signals.",
            ),
            (
                "Alkira fit is scored",
                "The research is mapped against Alkira's five solution categories "
                "and scored 1-5 stars based on evidence strength.",
            ),
            (
                "You get a brief",
                "Complete with proof points, strategic sales questions tied to "
                "real data, and source references you can verify.",
            ),
        ]
        for i, (title, desc) in enumerate(steps, 1):
            st.markdown(
                f'<div class="how-step">'
                f'<span class="how-step-num">{i}</span>'
                f'<span class="how-step-text">'
                f"<strong>{title}</strong><br/>{desc}"
                f"</span></div>",
                unsafe_allow_html=True,
            )

        st.caption("Briefs typically take 1-3 minutes to generate.")


if __name__ == "__main__":
    main()
