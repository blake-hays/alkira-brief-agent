"""
One-time setup: creates the Alkira Brief Generator agent and environment.
Run setup_skills.py first to upload the skill, then run this.

Usage:
    python setup_agent.py
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic
from system_prompt import ALKIRA_SYSTEM_PROMPT

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def main():
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env

    # ── Attach skill if available ────────────────────────────────
    skill_id = os.environ.get("ALKIRA_SKILL_ID", "")
    skills = []
    if skill_id:
        skills.append({"type": "custom", "skill_id": skill_id, "version": "latest"})
        print(f"Attaching skill: {skill_id}")
    else:
        print("Warning: ALKIRA_SKILL_ID not set. Run setup_skills.py first.")

    # ── Create the agent definition ──────────────────────────────
    print("Creating agent...")
    agent = client.beta.agents.create(
        name="Alkira Opportunity Brief Generator",
        description="Researches a company and produces a one-page Alkira opportunity brief as markdown.",
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

    # ── Save IDs to .env file ────────────────────────────────────
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "a") as f:
        f.write(f"\nALKIRA_AGENT_ID={agent.id}\n")
        f.write(f"ALKIRA_ENV_ID={environment.id}\n")

    print(f"\nSetup complete. IDs saved to {env_path}")
    print("You can now run: streamlit run app.py")


if __name__ == "__main__":
    main()
