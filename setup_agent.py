"""
One-time setup: creates the Alkira Brief Generator agent and environment.
Run setup_skills.py first to upload skills, then run this.

Usage:
    python setup_agent.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from system_prompt import ALKIRA_SYSTEM_PROMPT

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SKILL_ENV_KEYS = [
    "ALKIRA_CUSTOMER_SKILL_ID",
    "ALKIRA_BRIEF_TEMPLATE_SKILL_ID",
    # Legacy key from single-skill setup
    "ALKIRA_SKILL_ID",
]


def main():
    client = Anthropic()

    # ── Collect skill IDs ────────────────────────────────────────
    skills = []
    for key in SKILL_ENV_KEYS:
        skill_id = os.environ.get(key, "")
        if skill_id:
            skills.append({"type": "custom", "skill_id": skill_id, "version": "latest"})
            print(f"  Attaching skill: {key}={skill_id}")

    if not skills:
        print("Warning: No skill IDs found. Run setup_skills.py first.")

    # ── Create the agent definition ──────────────────────────────
    print("\nCreating agent...")
    agent = client.beta.agents.create(
        name="Alkira Opportunity Brief Generator",
        description=(
            "Researches a company and produces a scored Alkira opportunity brief "
            "with fit scoring, strategic sales questions, and source references."
        ),
        model="claude-sonnet-4-6",
        system=ALKIRA_SYSTEM_PROMPT,
        tools=[
            {
                "type": "agent_toolset_20260401",
                "configs": [
                    {"name": "write", "enabled": False},
                    {"name": "edit", "enabled": False},
                ],
            },
        ],
        skills=skills,
    )
    print(f"  Agent ID: {agent.id}")

    # ── Create the environment ───────────────────────────────────
    print("Creating environment...")
    environment = client.beta.environments.create(
        name="alkira-brief-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )
    print(f"  Environment ID: {environment.id}")

    # ── Save IDs to .env (overwrite old values) ──────────────────
    env_path = Path(__file__).parent / ".env"

    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text().splitlines()

    keys_to_replace = {"ALKIRA_AGENT_ID", "ALKIRA_ENV_ID"}
    filtered = [
        line for line in existing_lines
        if not any(line.startswith(f"{key}=") for key in keys_to_replace)
    ]
    filtered.append(f"ALKIRA_AGENT_ID={agent.id}")
    filtered.append(f"ALKIRA_ENV_ID={environment.id}")

    env_path.write_text("\n".join(filtered) + "\n")

    print(f"\nSetup complete. IDs saved to {env_path}")
    print("You can now run: streamlit run app.py")


if __name__ == "__main__":
    main()
