import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import export, llm, models, render

st.set_page_config(page_title="AI Portfolio Builder", page_icon="🌐", layout="wide")
SAMPLE = Path(__file__).parent / "samples" / "sample_profile.json"
TEXT_FIELDS, TABLES = models.TEXT_FIELDS, models.TABLES


# ---------- state helpers ----------
def to_df(rows, cols):
    return pd.DataFrame(rows, columns=cols).fillna("") if rows else pd.DataFrame(columns=cols)


def df_rows(df, cols):
    if df is None:
        return []
    return [{c: ("" if pd.isna(r[c]) else str(r[c])) for c in cols} for _, r in df.iterrows()]


def init():
    st.session_state.setdefault("ver", 0)
    st.session_state.setdefault("ai_error", "")
    st.session_state.setdefault("ai_ok", "")
    for f in TEXT_FIELDS:
        st.session_state.setdefault(f, "")
    for t, cols in TABLES.items():
        st.session_state.setdefault(f"{t}_src", to_df([], cols))
        st.session_state.setdefault(f"{t}_live", to_df([], cols))


def collect() -> dict:
    p = {f: st.session_state.get(f, "") for f in TEXT_FIELDS}
    for t, cols in TABLES.items():
        p[t] = df_rows(st.session_state.get(f"{t}_live"), cols)
    return models.normalize_profile(p)


def load_profile(data: dict):
    p = models.normalize_profile(data)
    for f in TEXT_FIELDS:
        st.session_state[f] = p[f]
    for t, cols in TABLES.items():
        df = to_df(p[t], cols)
        st.session_state[f"{t}_src"] = df
        st.session_state[f"{t}_live"] = df
    st.session_state.ver += 1


def load_sample():
    load_profile(json.loads(SAMPLE.read_text(encoding="utf-8")))


def _ai_settings():
    return st.session_state.get("model", "llama3.2"), st.session_state.get("host"), st.session_state.get("temp", 0.5)


def ai_copy():
    st.session_state.ai_error = st.session_state.ai_ok = ""
    model, host, temp = _ai_settings()
    try:
        out = llm.generate_copy(collect(), model, host, temp)
        if out["tagline"]:
            st.session_state.tagline = out["tagline"]
        if out["about"]:
            st.session_state.about = out["about"]
        st.session_state.ai_ok = "Tagline and About section updated. Review and edit them."
    except Exception as e:
        st.session_state.ai_error = f"Could not reach Ollama: {e}"


def ai_projects():
    st.session_state.ai_error = st.session_state.ai_ok = ""
    model, host, temp = _ai_settings()
    p = collect()
    if not p["projects"]:
        st.session_state.ai_error = "Add at least one project first."
        return
    try:
        new = llm.improve_projects(p, model, host, temp)
        rows = [{**row, "description": d} for row, d in zip(p["projects"], new)]
        df = to_df(rows, TABLES["projects"])
        st.session_state.projects_src = df
        st.session_state.projects_live = df
        st.session_state.ver += 1
        st.session_state.ai_ok = "Project descriptions rewritten. Review and edit them."
    except Exception as e:
        st.session_state.ai_error = f"Could not reach Ollama: {e}"


init()

# ---------- sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    host = st.text_input("Ollama host", value="http://localhost:11434", key="host")
    installed = llm.list_models(host)
    if installed:
        st.selectbox("Model", installed, key="model")
    else:
        st.text_input("Model", value="llama3.2", key="model")
        st.warning("Ollama not detected. You can still build and download your site without AI.")
    st.slider("Creativity", 0.0, 1.0, 0.5, 0.1, key="temp")
    st.divider()
    theme = st.selectbox("Theme", list(render.THEMES))
    accent = st.color_picker("Accent colour", render.DEFAULT_ACCENT)
    st.divider()
    st.button("Load sample data", on_click=load_sample, use_container_width=True)
    up = st.file_uploader("Upload saved profile (.json)", type="json")
    if up is not None and st.session_state.get("loaded_upload") != (up.name, up.size):
        try:
            load_profile(json.loads(up.getvalue().decode("utf-8")))
            st.session_state.loaded_upload = (up.name, up.size)
            st.rerun()
        except (ValueError, UnicodeDecodeError):
            st.error("That file is not a valid profile JSON.")
    st.caption("Everything runs locally. Nothing is uploaded.")

st.title("🌐 AI Portfolio Builder")
st.caption("Fill in your details, let a local AI polish the writing, and download a ready-to-publish portfolio website.")

profile = collect()
comp = models.completeness(profile)
m1, m2 = st.columns([1, 3])
m1.metric("Profile completeness", f"{comp['score']}%")
with m2:
    st.progress(comp["score"] / 100)
    if comp["tips"]:
        st.caption("To improve: " + " · ".join(comp["tips"][:3]))

if st.session_state.ai_error:
    st.error(st.session_state.ai_error)
if st.session_state.ai_ok:
    st.success(st.session_state.ai_ok)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["1 · Basics", "2 · Skills & links", "3 · Projects", "4 · Experience & education", "5 · Preview & export"])
ver = st.session_state.ver

with tab1:
    a, b = st.columns(2)
    a.text_input("Full name", key="name")
    b.text_input("Job title", key="title", placeholder="Data Analyst")
    a.text_input("Location", key="location")
    b.text_input("Email", key="email")
    st.text_input("Tagline", key="tagline", placeholder="One line about what you do")
    st.text_area("About you", key="about", height=180)
    st.button("✨ Write my tagline and About with AI", on_click=ai_copy,
              help="Uses your skills, projects and education. Fill those in first for better results.")

with tab2:
    st.text_area("Skills (one group per line, like `Languages: Python, SQL`)", key="skills", height=160)
    a, b, c = st.columns(3)
    a.text_input("GitHub URL", key="github", placeholder="github.com/your-username")
    b.text_input("LinkedIn URL", key="linkedin")
    c.text_input("Personal website", key="website")
    st.text_area("Certifications (one per line)", key="certifications", height=100)

with tab3:
    st.caption("Add a row per project. Separate tools with commas.")
    cfg = {"description": st.column_config.TextColumn(width="large"), "tech": st.column_config.TextColumn("Tech (comma separated)"),
           "github": st.column_config.TextColumn("GitHub URL"), "demo": st.column_config.TextColumn("Live demo URL")}
    st.session_state.projects_live = st.data_editor(
        st.session_state.projects_src, num_rows="dynamic", use_container_width=True, column_config=cfg, key=f"projects_{ver}")
    st.button("✨ Improve project descriptions with AI", on_click=ai_projects)

with tab4:
    st.subheader("Experience")
    st.caption("Put bullet points in Details, separated by `;`")
    st.session_state.experience_live = st.data_editor(
        st.session_state.experience_src, num_rows="dynamic", use_container_width=True,
        column_config={"details": st.column_config.TextColumn(width="large")}, key=f"experience_{ver}")
    st.subheader("Education")
    st.session_state.education_live = st.data_editor(
        st.session_state.education_src, num_rows="dynamic", use_container_width=True, key=f"education_{ver}")

with tab5:
    profile = collect()
    site = render.render(profile, theme, accent)
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇️ index.html", site, "index.html", "text/html", use_container_width=True)
    d2.download_button("⬇️ Site bundle (.zip)", export.build_zip(profile, site), "portfolio_site.zip", "application/zip", use_container_width=True)
    d3.download_button("💾 Save profile (.json)", export.profile_json(profile), "my_profile.json", "application/json", use_container_width=True)
    with st.expander("How to publish for free on GitHub Pages"):
        st.markdown(
            "1. Create a GitHub repo named `<your-username>.github.io`.\n"
            "2. Upload `index.html` from the zip.\n"
            "3. Repo → Settings → Pages → Deploy from branch → `main` / root.\n"
            "4. Your site goes live at `https://<your-username>.github.io/` in about a minute.")
    components.html(site, height=800, scrolling=True)
