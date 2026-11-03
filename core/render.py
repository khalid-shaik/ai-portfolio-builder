"""Render a profile into a single self-contained, responsive HTML page."""
import html
import json
import re
from datetime import datetime
from urllib.parse import urlparse

from .models import normalize_profile

THEMES = {
    "Midnight": {"bg": "#0b1020", "surface": "#141b34", "text": "#e6e9f5", "muted": "#9aa3c0", "border": "#262f55"},
    "Clean Light": {"bg": "#f7f8fa", "surface": "#ffffff", "text": "#1b1f24", "muted": "#5b6570", "border": "#e3e6ea"},
    "Sunset": {"bg": "#1a1022", "surface": "#2a1833", "text": "#fff2ee", "muted": "#d3b7c4", "border": "#4a2a52"},
}
DEFAULT_ACCENT = "#6c8cff"
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def safe_url(u: str) -> str:
    """Return a safe http(s) URL or '' (blocks javascript:, data:, mailto: etc.)."""
    u = (u or "").strip()
    if not u:
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*:", u, re.I) and not u.lower().startswith(("http://", "https://")):
        return ""
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    p = urlparse(u)
    return u if p.scheme in ("http", "https") and p.netloc and " " not in u else ""


def split_list(s: str, bullets: bool = False) -> list[str]:
    pattern = r"[;\n]" if bullets else r"[,;\n]"
    return [x.strip(" -•\t") for x in re.split(pattern, s or "") if x.strip(" -•\t")]


def parse_skills(text: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        if ":" in line:
            cat, items = line.split(":", 1)
            groups.setdefault(cat.strip() or "Skills", []).extend(split_list(items))
        else:
            groups.setdefault("Skills", []).extend(split_list(line))
    return {k: v for k, v in groups.items() if v}


CSS = """
:root{--bg:__BG__;--surface:__SURFACE__;--text:__TEXT__;--muted:__MUTED__;--border:__BORDER__;--accent:__ACCENT__}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:980px;margin:0 auto;padding:0 20px}
nav{position:sticky;top:0;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);z-index:5}
nav .wrap{display:flex;gap:18px;align-items:center;overflow-x:auto;padding-top:12px;padding-bottom:12px}
nav a{color:var(--muted);font-size:.92rem;white-space:nowrap}nav a:hover{color:var(--text);text-decoration:none}
nav .brand{color:var(--text);font-weight:700;margin-right:auto}
.hero{padding:84px 0 56px;display:flex;gap:28px;align-items:center;flex-wrap:wrap}
.avatar{width:96px;height:96px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-size:2rem;font-weight:700;flex:none}
h1{margin:0;font-size:clamp(2rem,5vw,3rem);line-height:1.15}
.role{color:var(--accent);font-weight:600;font-size:1.15rem;margin:.2rem 0}
.tagline{color:var(--muted);max-width:620px;margin:.4rem 0 1rem}
.btns{display:flex;gap:10px;flex-wrap:wrap}
.btn{border:1px solid var(--border);background:var(--surface);color:var(--text);padding:8px 16px;border-radius:999px;font-size:.92rem}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}.btn:hover{text-decoration:none;filter:brightness(1.1)}
section{padding:44px 0;border-top:1px solid var(--border)}
h2{margin:0 0 20px;font-size:1.5rem}h2::after{content:"";display:block;width:44px;height:3px;background:var(--accent);margin-top:8px;border-radius:2px}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:var(--surface);border:1px solid var(--border);padding:3px 12px;border-radius:999px;font-size:.85rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:18px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:10px}
.card h3{margin:0;font-size:1.1rem}.card p{margin:0;color:var(--muted)}.links{display:flex;gap:14px;margin-top:auto;font-size:.9rem}
.skillgroup{margin-bottom:16px}.skillgroup h3{margin:0 0 8px;font-size:.95rem;color:var(--muted);font-weight:600}
.item{margin-bottom:22px;padding-left:16px;border-left:3px solid var(--accent)}
.item h3{margin:0;font-size:1.05rem}.meta{color:var(--muted);font-size:.9rem}.item ul{margin:8px 0 0;padding-left:18px;color:var(--muted)}
footer{border-top:1px solid var(--border);padding:28px 0;color:var(--muted);font-size:.9rem;text-align:center}
@media print{nav,.btns{display:none}body{background:#fff;color:#000}}
"""


def _links(*pairs) -> str:
    out = []
    for label, url in pairs:
        u = safe_url(url)
        if u:
            out.append(f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>')
    return "".join(out)


def render(profile: dict, theme: str = "Midnight", accent: str = DEFAULT_ACCENT) -> str:
    p = normalize_profile(profile)
    t = THEMES.get(theme, THEMES["Midnight"])
    accent = accent if _HEX.match(accent or "") else DEFAULT_ACCENT
    css = CSS.replace("__ACCENT__", accent)
    for k, v in t.items():
        css = css.replace(f"__{k.upper()}__", v)

    name = p["name"] or "Your Name"
    initials = "".join(w[0] for w in name.split()[:2]).upper() or "?"
    gh, li, web = safe_url(p["github"]), safe_url(p["linkedin"]), safe_url(p["website"])
    email = p["email"] if re.match(r"^[^\s@<>\"']+@[^\s@<>\"']+\.[^\s@<>\"']+$", p["email"]) else ""

    btns = []
    if email:
        btns.append(f'<a class="btn primary" href="mailto:{esc(email)}">Contact me</a>')
    for label, u in (("GitHub", gh), ("LinkedIn", li), ("Website", web)):
        if u:
            btns.append(f'<a class="btn" href="{esc(u)}" target="_blank" rel="noopener noreferrer">{label}</a>')

    sections, nav = [], []

    def add(sec_id, label, body):
        if body:
            nav.append(f'<a href="#{sec_id}">{label}</a>')
            sections.append(f'<section id="{sec_id}"><div class="wrap"><h2>{label}</h2>{body}</div></section>')

    if p["about"]:
        paras = "".join(f"<p>{esc(x)}</p>" for x in p["about"].split("\n") if x.strip())
        add("about", "About", paras)

    groups = parse_skills(p["skills"])
    add("skills", "Skills", "".join(
        f'<div class="skillgroup"><h3>{esc(cat)}</h3><div class="chips">'
        + "".join(f'<span class="chip">{esc(i)}</span>' for i in items) + "</div></div>"
        for cat, items in groups.items()))

    cards = []
    for pr in p["projects"]:
        chips = "".join(f'<span class="chip">{esc(x)}</span>' for x in split_list(pr["tech"]))
        cards.append(
            f'<article class="card"><h3>{esc(pr["title"] or "Untitled project")}</h3><p>{esc(pr["description"])}</p>'
            f'<div class="chips">{chips}</div><div class="links">{_links(("Code", pr["github"]), ("Live demo", pr["demo"]))}</div></article>')
    add("projects", "Projects", f'<div class="grid">{"".join(cards)}</div>' if cards else "")

    def timeline(rows, head, sub):
        out = []
        for r in rows:
            lis = "".join(f"<li>{esc(b)}</li>" for b in split_list(r["details"], bullets=True))
            out.append(f'<div class="item"><h3>{esc(head(r))}</h3><div class="meta">{esc(sub(r))}</div>'
                       + (f"<ul>{lis}</ul>" if lis else "") + "</div>")
        return "".join(out)

    add("experience", "Experience", timeline(
        p["experience"], lambda r: " · ".join(x for x in (r["role"], r["company"]) if x), lambda r: r["period"]))
    add("education", "Education", timeline(
        p["education"], lambda r: r["degree"], lambda r: " · ".join(x for x in (r["institution"], r["year"]) if x)))
    certs = split_list(p["certifications"])
    add("certifications", "Certifications", f'<div class="chips">{"".join(f"<span class=chip>{esc(c)}</span>" for c in certs)}</div>' if certs else "")

    desc = p["tagline"] or p["about"][:155] or f"Portfolio of {name}"
    ld = {"@context": "https://schema.org", "@type": "Person", "name": name, "jobTitle": p["title"],
          "email": email, "url": web, "address": p["location"], "sameAs": [u for u in (gh, li) if u]}
    ld = json.dumps({k: v for k, v in ld.items() if v}).replace("<", "\\u003c").replace(">", "\\u003e")
    title = f"{name} | {p['title']}" if p["title"] else name

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website">
<script type="application/ld+json">{ld}</script>
<style>{css}</style></head><body>
<nav><div class="wrap"><span class="brand">{esc(name)}</span>{"".join(nav)}</div></nav>
<header class="wrap hero"><div class="avatar">{esc(initials)}</div><div>
<h1>{esc(name)}</h1><div class="role">{esc(p["title"])}{" · " + esc(p["location"]) if p["location"] else ""}</div>
<p class="tagline">{esc(p["tagline"])}</p><div class="btns">{"".join(btns)}</div></div></header>
{"".join(sections)}
<footer>&copy; {datetime.now().year} {esc(name)}. Built with AI Portfolio Builder.</footer>
</body></html>"""
