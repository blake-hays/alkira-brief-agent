"""
One-time setup: creates the Alkira Brief Generator agent and environment.
Run this once, then save the IDs to .env for generate_brief.py to use.

Usage:
    python setup_agent.py
"""

import os
import json
from anthropic import Anthropic
from system_prompt import ALKIRA_KNOWLEDGE_BASE

def main():
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env

    # ── Create the agent definition ──────────────────────────────
    print("Creating agent...")
    agent = client.beta.agents.create(
        name="Alkira Opportunity Brief Generator",
        description="Researches a company and produces a one-page Alkira opportunity brief as a .docx file.",
        model="claude-sonnet-4-6",
        system=ALKIRA_KNOWLEDGE_BASE,
        tools=[
            {"type": "agent_toolset_20260401"}   # gives the agent: bash, file ops, web search
        ],
    )
    print(f"  Agent ID: {agent.id}")

    # ── Create the environment ───────────────────────────────────
    print("Creating environment...")
    environment = client.beta.environments.create(
        name="alkira-brief-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},  # agent needs web search access
        },
    )
    print(f"  Environment ID: {environment.id}")

    # ── Save IDs to .env file ────────────────────────────────────
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "a") as f:
        f.write(f"\nALKIRA_AGENT_ID={agent.id}\n")
        f.write(f"ALKIRA_ENV_ID={environment.id}\n")

    print(f"\nSetup complete. IDs saved to {env_path}")
    print("You can now run: python generate_brief.py 'Company Name'")


if __name__ == "__main__":
    main()
