"""
Upload the alkira-customer skill to Anthropic's Skills API.
Run this once (or when updating the skill), then run setup_agent.py.

Usage:
    python setup_skills.py
"""

import os
from pathlib import Path
from anthropic import Anthropic

SKILL_DIR = Path(__file__).parent / "skills" / "alkira-customer"


def main():
    client = Anthropic()  # reads ANTHROPIC_API_KEY from env

    # Collect skill files with relative paths
    files = []
    for file_path in sorted(SKILL_DIR.rglob("*")):
        if file_path.is_file():
            rel_path = f"alkira-customer/{file_path.relative_to(SKILL_DIR)}"
            files.append((rel_path, file_path.read_bytes(), "text/markdown"))

    print(f"Uploading {len(files)} files:")
    for name, _, _ in files:
        print(f"  {name}")

    skill = client.beta.skills.create(
        display_title="Alkira Customer Knowledge Base",
        files=files,
        betas=["skills-2025-10-02"],
    )

    print(f"\nSkill ID: {skill.id}")

    # Save to .env
    env_path = Path(__file__).parent / ".env"
    with open(env_path, "a") as f:
        f.write(f"\nALKIRA_SKILL_ID={skill.id}\n")

    print(f"Saved to {env_path}")
    print("Now run: python setup_agent.py")


if __name__ == "__main__":
    main()
