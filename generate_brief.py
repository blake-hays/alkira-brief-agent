"""
Generate an Alkira opportunity brief for any company.

Usage:
    python generate_brief.py "Mary Kay"
    python generate_brief.py "Walmart" --output walmart_brief.md
    python generate_brief.py "Chevron" --verbose
"""

import os
import sys
import argparse
import time
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

AGENT_ID = os.environ.get("ALKIRA_AGENT_ID")
ENV_ID = os.environ.get("ALKIRA_ENV_ID")


def generate_brief(company_name: str, output_path: str = None, verbose: bool = False):
    """Create a session, send the company name, stream the agent's work, print the brief."""

    if not AGENT_ID or not ENV_ID:
        print("Error: ALKIRA_AGENT_ID and ALKIRA_ENV_ID must be set.")
        print("Run setup_agent.py first.")
        sys.exit(1)

    client = Anthropic()

    # ── Start a new session ──────────────────────────────────────
    print(f"\nStarting brief generation for: {company_name}")
    print("=" * 50)

    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENV_ID,
        title=f"Alkira Brief: {company_name}",
    )

    if verbose:
        print(f"Session ID: {session.id}")

    # ── Send the prompt ──────────────────────────────────────────
    prompt = (
        f'Research the company "{company_name}" and generate a one-page Alkira '
        f"opportunity brief. Follow the brief structure and writing style in your "
        f"instructions exactly. Focus on information from the past 12 months. "
        f"Return the brief as markdown text."
    )

    print(f"\nAgent is researching {company_name}...")
    print("This typically takes 1-2 minutes.\n")

    # ── Stream events ────────────────────────────────────────────
    text_parts: list[str] = []
    start = time.time()
    timeout_seconds = 300  # 5 minutes

    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            # Send user message after opening the stream (per docs)
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
                if time.time() - start > timeout_seconds:
                    print("\nTimed out after 5 minutes.")
                    break

                if not hasattr(event, "type"):
                    continue

                # Capture agent text
                if event.type == "agent.message":
                    for block in getattr(event, "content", []):
                        if getattr(block, "type", None) == "text":
                            text_parts.append(block.text)
                            if verbose:
                                print(block.text, end="", flush=True)

                # Track tool use for status updates
                if event.type == "agent.tool_use":
                    tool_name = getattr(event, "name", "unknown")
                    if "search" in tool_name:
                        print("  [searching the web...]")

                if event.type == "session.status_idle":
                    break

                if event.type == "session.error":
                    msg = getattr(getattr(event, "error", None), "message", "unknown")
                    print(f"\n[Error: {msg}]")
                    break

    finally:
        # Delete session to stop billing and release resources
        try:
            client.beta.sessions.delete(session.id)
        except Exception:
            pass

    elapsed = time.time() - start
    print(f"\nCompleted in {elapsed:.0f} seconds.")

    brief = "".join(text_parts)

    # ── Output ───────────────────────────────────────────────────
    if not verbose:
        print(brief)

    if output_path:
        with open(output_path, "w") as f:
            f.write(brief)
        print(f"\nBrief saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate an Alkira opportunity brief for a target company."
    )
    parser.add_argument("company", help="Company name (e.g., 'Mary Kay', 'Walmart')")
    parser.add_argument("--output", "-o", help="Output filename (e.g., brief.md)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show agent output in real-time")

    args = parser.parse_args()
    generate_brief(args.company, args.output, args.verbose)


if __name__ == "__main__":
    main()
