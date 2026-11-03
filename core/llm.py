"""Local LLM helpers (Ollama) that write portfolio copy from the user's own facts."""
import json
import re

import ollama

SYSTEM = (
    "You write concise, honest portfolio copy for early-career professionals. Use ONLY the facts provided. "
    "Never invent employers, numbers, awards, degrees or skills. Reply with a single valid JSON object only."
)


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise ValueError("Model did not return JSON.")
        return json.loads(m.group(0))


def facts(p: dict) -> str:
    lines = [f"Name: {p['name']}", f"Title: {p['title']}", f"Location: {p['location']}",
             f"Skills: {p['skills'].replace(chr(10), '; ')}", f"Current about text: {p['about']}"]
    for pr in p["projects"]:
        lines.append(f"Project: {pr['title']} | tech: {pr['tech']} | notes: {pr['description']}")
    for e in p["experience"]:
        lines.append(f"Experience: {e['role']} at {e['company']} ({e['period']}) {e['details']}")
    for e in p["education"]:
        lines.append(f"Education: {e['degree']}, {e['institution']} {e['year']}")
    if p["certifications"]:
        lines.append("Certifications: " + p["certifications"].replace("\n", "; "))
    return "\n".join(lines)


def normalize_copy(d: dict) -> dict:
    return {"tagline": str(d.get("tagline", "")).strip().strip('"'), "about": str(d.get("about", "")).strip()}


def normalize_projects(d: dict, originals: list[str]) -> list[str]:
    out = list(originals)
    items = d.get("projects") if isinstance(d.get("projects"), list) else []
    for pos, it in enumerate(items):
        if not isinstance(it, dict) or not str(it.get("description", "")).strip():
            continue
        try:
            idx = int(it.get("index", pos))
        except (TypeError, ValueError):
            idx = pos
        if 0 <= idx < len(out):
            out[idx] = str(it["description"]).strip()
    return out


def list_models(host: str | None = None) -> list[str]:
    try:
        client = ollama.Client(host=host) if host else ollama.Client()
        resp = client.list()
        models = resp["models"] if isinstance(resp, dict) else resp.models
        return sorted((m["model"] if isinstance(m, dict) else m.model) for m in models)
    except Exception:
        return []


def _chat(prompt: str, model: str, host: str | None, temperature: float) -> dict:
    client = ollama.Client(host=host) if host else ollama.Client()
    resp = client.chat(
        model=model,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        format="json",
        options={"temperature": temperature},
    )
    content = resp["message"]["content"] if isinstance(resp, dict) else resp.message.content
    return parse_json(content)


def generate_copy(profile: dict, model="llama3.2", host=None, temperature=0.5) -> dict:
    prompt = (
        f"FACTS ABOUT THE PERSON:\n{facts(profile)}\n\n"
        'Write a one-line tagline (max 15 words) and an "about" section (3-4 sentences, first person, warm and professional, '
        "mention strongest skills and projects). "
        'Return JSON: {"tagline": "...", "about": "..."}'
    )
    return normalize_copy(_chat(prompt, model, host, temperature))


def improve_projects(profile: dict, model="llama3.2", host=None, temperature=0.4) -> list[str]:
    originals = [p["description"] for p in profile["projects"]]
    listing = "\n".join(
        f"{i}. {p['title']} | tech: {p['tech']} | notes: {p['description']}" for i, p in enumerate(profile["projects"]))
    prompt = (
        f"PROJECTS:\n{listing}\n\nRewrite each project description in 2 clear sentences: what it does, how it was built, "
        "and the tools used. Do not add metrics or features that are not in the notes. "
        'Return JSON: {"projects": [{"index": 0, "description": "..."}]}'
    )
    return normalize_projects(_chat(prompt, model, host, temperature), originals)
