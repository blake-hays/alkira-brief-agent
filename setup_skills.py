"""
Upload skills to Anthropic's Skills API.
Run this once (or when updating skills), then run setup_agent.py.

Uploads two skills:
  1. alkira-customer — Alkira knowledge base (entry points, proof points, etc.)
  2. alkira-brief-template — Brief structure, scoring rubric, research checklist

If a skill with the same title already exists, the script reuses
the existing ID from .env instead of re-uploading.

Usage:
    python setup_skills.py
    python setup_skills.py --force   # re-upload even if IDs exist
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SKILLS_ROOT = Path(__file__).parent / "skills"

def _versioned_title(base: str) -> str:
    """Append a timestamp to the title so the Skills API accepts re-uploads."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base} ({ts})"


SKILLS_TO_UPLOAD = [
    {
        "dir": "alkira-customer",
        "base_title": "Alkira Customer Knowledge Base",
        "env_key": "ALKIRA_CUSTOMER_SKILL_ID",
        "legacy_key": "ALKIRA_SKILL_ID",
    },
    {
        "dir": "alkira-brief-template",
        "base_title": "Alkira Brief Template and Scoring",
        "env_key": "ALKIRA_BRIEF_TEMPLATE_SKILL_ID",
        "legacy_key": None,
    },
    {
        "dir": "stop-slop",
        "base_title": "Stop Slop Writing Quality Filter",
        "env_key": "STOP_SLOP_SKILL_ID",
        "legacy_key": None,
    },
]


@dataclass(frozen=True)
class UploadedSkill:
    name: str
    skill_id: str
    env_key: str


def upload_skill(client: Anthropic, skill_dir: str, title: str) -> str:
    """Upload a single skill directory and return its ID."""
    skill_path = SKILLS_ROOT / skill_dir
    files = []
    for file_path in sorted(skill_path.rglob("*")):
        if file_path.is_file():
            rel_path = f"{skill_dir}/{file_path.relative_to(skill_path)}"
            files.append((rel_path, file_path.read_bytes(), "text/markdown"))

    print(f"  Uploading {len(files)} files for '{title}':")
    for name, _, _ in files:
        print(f"    {name}")

    skill = client.beta.skills.create(
        display_title=title,
        files=files,
        betas=["skills-2025-10-02"],
    )
    return skill.id


def get_existing_id(spec: dict) -> str:
    """Check .env for an existing skill ID (current key or legacy key)."""
    skill_id = os.environ.get(spec["env_key"], "")
    if not skill_id and spec.get("legacy_key"):
        skill_id = os.environ.get(spec["legacy_key"], "")
    return skill_id


def save_env_vars(uploaded: list[UploadedSkill]) -> None:
    """Write skill IDs to .env, replacing old values."""
    env_path = Path(__file__).parent / ".env"

    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text().splitlines()

    # Keys to replace (including legacy)
    keys_to_replace = {s.env_key for s in uploaded}
    keys_to_replace.add("ALKIRA_SKILL_ID")  # remove legacy key

    filtered = [
        line for line in existing_lines
        if not any(line.startswith(f"{key}=") for key in keys_to_replace)
    ]

    for s in uploaded:
        filtered.append(f"{s.env_key}={s.skill_id}")

    env_path.write_text("\n".join(filtered) + "\n")


def main():
    force = "--force" in sys.argv
    client = Anthropic()
    uploaded: list[UploadedSkill] = []

    print("Setting up skills...\n")

    for spec in SKILLS_TO_UPLOAD:
        existing_id = get_existing_id(spec)
        base_title = spec["base_title"]

        if existing_id and not force:
            print(f"  '{base_title}' — reusing existing ID: {existing_id}")
            print(f"    (run with --force to re-upload)\n")
            uploaded.append(UploadedSkill(
                name=spec["dir"],
                skill_id=existing_id,
                env_key=spec["env_key"],
            ))
            continue

        # Use versioned title to avoid "duplicate display_title" errors
        title = _versioned_title(base_title) if force else base_title

        try:
            skill_id = upload_skill(client, spec["dir"], title)
            print(f"  Skill ID: {skill_id}\n")
            uploaded.append(UploadedSkill(
                name=spec["dir"],
                skill_id=skill_id,
                env_key=spec["env_key"],
            ))
        except Exception as exc:
            if "reuse an existing display_title" in str(exc):
                # Retry with versioned title
                title = _versioned_title(base_title)
                print(f"  Title conflict. Retrying as '{title}'...")
                skill_id = upload_skill(client, spec["dir"], title)
                print(f"  Skill ID: {skill_id}\n")
                uploaded.append(UploadedSkill(
                    name=spec["dir"],
                    skill_id=skill_id,
                    env_key=spec["env_key"],
                ))
            else:
                raise

    save_env_vars(uploaded)

    env_path = Path(__file__).parent / ".env"
    print(f"Skill IDs saved to {env_path}")
    for s in uploaded:
        print(f"  {s.env_key}={s.skill_id}")

    print("\nNow run: python setup_agent.py")


if __name__ == "__main__":
    main()
