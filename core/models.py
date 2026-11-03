"""Profile data model: plain dicts of strings, easy to save as JSON."""
TEXT_FIELDS = ["name", "title", "location", "email", "tagline", "about",
               "github", "linkedin", "website", "skills", "certifications"]
TABLES = {
    "projects": ["title", "description", "tech", "github", "demo"],
    "experience": ["role", "company", "period", "details"],
    "education": ["degree", "institution", "year", "details"],
}


def _s(v) -> str:
    if isinstance(v, (list, tuple)):
        return "\n".join(str(x).strip() for x in v if str(x).strip())
    return "" if v is None else str(v).strip()


def normalize_profile(d: dict | None) -> dict:
    d = d if isinstance(d, dict) else {}
    out = {f: _s(d.get(f)) for f in TEXT_FIELDS}
    for table, cols in TABLES.items():
        rows = []
        for r in d.get(table) or []:
            if isinstance(r, dict):
                row = {c: _s(r.get(c)) for c in cols}
                if any(row.values()):
                    rows.append(row)
        out[table] = rows
    return out


def completeness(p: dict) -> dict:
    """Return a 0-100 score and tips for improving the profile."""
    p = normalize_profile(p)
    checks = [
        (bool(p["name"]), 10, "Add your name."),
        (bool(p["title"]), 10, "Add a job title, e.g. 'Data Analyst'."),
        (len(p["about"]) >= 80, 15, "Write an About section of at least 80 characters."),
        (len([x for x in p["skills"].replace(",", "\n").split("\n") if x.strip()]) >= 5, 10, "List at least 5 skills."),
        (len(p["projects"]) >= 2, 20, "Add at least 2 projects."),
        (any(r["github"] or r["demo"] for r in p["projects"]), 10, "Link a GitHub or demo URL on a project."),
        (bool(p["github"] or p["linkedin"]), 10, "Add your GitHub or LinkedIn link."),
        (bool(p["email"]), 5, "Add a contact email."),
        (bool(p["education"] or p["experience"]), 10, "Add education or experience."),
    ]
    score = sum(w for ok, w, _ in checks if ok)
    return {"score": score, "tips": [t for ok, _, t in checks if not ok]}
