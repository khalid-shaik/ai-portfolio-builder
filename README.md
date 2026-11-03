# 🌐 AI Portfolio Builder

**Project 2 of 60 AI agents.** Enter your details, let a local AI polish the writing, and download a **ready-to-publish portfolio website** (single `index.html`, no build step, free hosting on GitHub Pages).

## Features
- Guided form: basics, skills, links, projects, experience, education, certifications
- **AI writing (Ollama, local):** tagline + About section, and rewritten project descriptions, using only the facts you provide
- Works **without AI** too: build and download the site even if Ollama is not running
- 3 themes + custom accent colour, responsive layout, SEO tags and structured data
- Profile completeness score with tips
- Save/load your profile as JSON; export `index.html` or a deploy-ready `.zip`
- Safe output: all text is HTML-escaped and only `http(s)` links are allowed

## Tech stack
Python · Streamlit · Ollama · pandas · pytest · GitHub Actions

## Quick start
```powershell
ollama pull llama3.2
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Click **Load sample data** in the sidebar to see a full example. A pre-built sample is in `samples/sample_site.html`.

## Publish your site
1. Download the **Site bundle (.zip)** from the last tab.
2. Create a GitHub repo named `<your-username>.github.io` and upload `index.html`.
3. Repo → Settings → Pages → Deploy from branch → `main` / root.

## Project structure
```
app.py             Streamlit UI (5 tabs)
core/models.py     profile schema, normalisation, completeness score
core/render.py     profile -> HTML (themes, escaping, URL safety)
core/llm.py        Ollama prompts + JSON validation
core/export.py     zip bundle and profile JSON
tests/             pytest unit and UI tests
samples/           sample profile and generated site
```

## Tests
```bash
pytest -q
```

## Roadmap
- [ ] Import details from a resume PDF (reuse Project 1 parser)
- [ ] More themes and a dark/light toggle
- [ ] Project screenshots/images
