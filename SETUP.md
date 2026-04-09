# Alkira Brief Generator — Web App

A web app where partners type a company name and get a downloadable one-page Alkira opportunity brief (.docx). Powered by Claude Managed Agents.

The agent researches the company via web search, maps findings to Alkira's entry points, and generates a formatted Word document. Partners see a progress bar and download button.

## Prerequisites

- Python 3.10+
- An Anthropic API key with Managed Agents beta access

## Setup

```bash
cd alkira-brief-agent

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY

# 3. Create the agent definition (one time)
python setup_agent.py

# 4. Launch the web app
streamlit run app.py
```

The app opens at http://localhost:8501. Partners type a company name, hit "Generate Brief," and get a .docx download when the agent finishes.

## File Overview

| File | Purpose |
|------|---------|
| `app.py` | Streamlit web app (the frontend partners use) |
| `setup_agent.py` | One-time setup: creates agent + environment on Anthropic's platform |
| `generate_brief.py` | CLI alternative (if you prefer terminal usage) |
| `system_prompt.py` | Alkira knowledge base embedded as the agent's system prompt |
| `.env` | API key + agent/environment IDs (git-ignored) |

## Model Choice

The agent uses **claude-sonnet-4-6** by default. This is the right call for this task. The agent is doing structured web research and templated document generation, not deep multi-step reasoning. Sonnet handles this at the same quality as Opus, 5x faster, and at 1/5 the token cost. At ~$0.15-0.40 per brief with Sonnet vs. ~$0.75-2.00 with Opus, the math is clear.

To change the model, edit `system_prompt.py` isn't where the model is set. Edit `setup_agent.py` and change the `model` parameter, then re-run it.

## Deployment Options

**Local (dev/demo):** `streamlit run app.py`

**Streamlit Community Cloud (free, fast):**
1. Push this folder to a GitHub repo
2. Go to share.streamlit.io, connect the repo
3. Set your secrets (ANTHROPIC_API_KEY, ALKIRA_AGENT_ID, ALKIRA_ENV_ID) in the Streamlit secrets panel
4. Deploy

**Cloud VM (production):**
```bash
# On any Linux VM with Python 3.10+
pip install -r requirements.txt
streamlit run app.py --server.port 8080 --server.address 0.0.0.0
```
Put it behind nginx or Cloudflare Tunnel for HTTPS.

## Cost Per Brief

- Standard Claude Sonnet 4.6 token rates (~$3/M input, $15/M output)
- $0.08/session hour (Managed Agents infrastructure)
- $0.01/web search query (agent runs ~5-10 searches per brief)
- Estimate: **~$0.15-0.40 per brief**

## Updating the Knowledge Base

Edit `system_prompt.py` to add case studies, update proof points, or change the brief template. Then re-run `python setup_agent.py` to create a new agent version with the updated prompt.

## Notes

- Managed Agents is in public beta (April 2026). The streaming and file download APIs may shift as the beta matures.
- The `sessions.files.read` call for downloading the generated docx is the most likely API surface to change. If auto-download breaks, the app shows the session ID so you can retrieve the file from the Anthropic Console.
- The agent installs `python-docx` inside its sandbox at runtime to generate the Word file. This adds a few seconds to the first run.
