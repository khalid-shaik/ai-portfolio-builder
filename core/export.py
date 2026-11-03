"""Package the generated site for download / GitHub Pages."""
import json
import zipfile
from io import BytesIO

from .models import normalize_profile

DEPLOY_README = """# My Portfolio

Generated with AI Portfolio Builder.

## Publish on GitHub Pages (free)
1. Create a new GitHub repo (use `<your-username>.github.io` for your main site URL).
2. Upload `index.html` and `.nojekyll` (or push this folder with git).
3. Repo -> Settings -> Pages -> Source: "Deploy from a branch" -> `main` / root -> Save.
4. After about a minute your site is live at `https://<your-username>.github.io/`.

## Edit later
Open `profile.json` in the AI Portfolio Builder (sidebar -> Upload profile), change what you need, and export again.
"""


def profile_json(profile: dict) -> str:
    return json.dumps(normalize_profile(profile), indent=2, ensure_ascii=False)


def build_zip(profile: dict, html_text: str) -> bytes:
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", html_text)
        z.writestr(".nojekyll", "")
        z.writestr("README.md", DEPLOY_README)
        z.writestr("profile.json", profile_json(profile))
    return buf.getvalue()
