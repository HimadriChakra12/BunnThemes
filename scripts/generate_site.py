#!/usr/bin/env python3
"""
generate_site.py

Walks the repository, finds every top-level "theme folder" that contains
one or more *.json theme files, and renders the listing rows in the form:

    ~/<Theme Folder>          (heading, level 5)
        ./<theme>.json        (clickable row)

Unlike the old version, this script does NOT own the whole of index.html
any more — index.html is a hand-built single-page app (Creator + Browse).
This script only replaces the content between the two marker comments:

    <!-- THEMES:START ... -->
    ...generated sections go here...
    <!-- THEMES:END -->

which live inside the Browse view's <main>. Everything else in index.html
(the Creator/Build/Submit UI, styles, scripts) is left untouched.

Usage: python3 scripts/generate_site.py
Output: index.html (theme listing section only, spliced in place)
"""

import json
import os
import sys
from pathlib import Path
from html import escape

# ---- config ---------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_FILE = REPO_ROOT / "index.html"

START_MARKER = "<!-- THEMES:START"
END_MARKER = "<!-- THEMES:END -->"

# Folders at repo root that are NOT theme folders
IGNORE_DIRS = {
    "Asset", ".github", ".git", "scripts", "node_modules",
}

GITHUB_USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "HimadriChakra12")
REPO_NAME = os.environ.get("GITHUB_REPO_NAME", "BunnThemes")
BRANCH = os.environ.get("GITHUB_DEFAULT_BRANCH", "main")

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}"
BLOB_BASE = f"https://github.com/{GITHUB_USER}/{REPO_NAME}/blob/{BRANCH}"


# ---- collect theme data -----------------------------------------------------

def find_theme_folders():
    folders = []
    for entry in sorted(REPO_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if entry.name in IGNORE_DIRS or entry.name.startswith("."):
            continue
        json_files = sorted(entry.rglob("*.json"))
        if not json_files:
            continue
        files = []
        for jf in json_files:
            rel_to_theme = jf.relative_to(entry).as_posix()
            rel_to_repo = jf.relative_to(REPO_ROOT).as_posix()
            theme_name = None
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                theme_name = data.get("name")
            except Exception:
                pass
            files.append({
                "display": f"./{rel_to_theme}",
                "raw_url": f"{RAW_BASE}/{rel_to_repo}",
                "blob_url": f"{BLOB_BASE}/{rel_to_repo}",
                "name": theme_name,
            })
        folders.append({"folder": entry.name, "files": files})
    return folders


# ---- render just the theme-list markup --------------------------------------

def render_sections(folders):
    sections = []
    for f in folders:
        rows = []
        for file in f["files"]:
            label = file["name"] or file["display"]
            rows.append(f"""
        <li class="file-row"
            data-raw="{escape(file['raw_url'])}"
            data-blob="{escape(file['blob_url'])}"
            tabindex="0"
            role="button"
            aria-label="Copy URL and open {escape(file['display'])}">
          <span class="file-path">{escape(file['display'])}</span>
          <span class="file-name">{escape(label)}</span>
          <span class="copied-tag">copied!</span>
        </li>""")

        sections.append(f"""
    <section class="theme-block">
      <h5 class="theme-heading">~/{escape(f['folder'])}</h5>
      <ul class="file-list">{''.join(rows)}
      </ul>
    </section>""")

    return "\n".join(sections)


# ---- splice into index.html --------------------------------------------------

def splice(html, generated_body):
    start_idx = html.find(START_MARKER)
    end_idx = html.find(END_MARKER)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        print(
            "error: could not find THEMES:START / THEMES:END markers in "
            f"{TARGET_FILE}. Refusing to touch the file — restore the "
            "marker comments inside <main> in the Browse view before "
            "running this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    # keep the opening marker line itself, replace everything up to (not
    # including) the closing marker line
    start_line_end = html.find("\n", start_idx) + 1
    return html[:start_line_end] + generated_body.lstrip("\n") + "\n" + html[end_idx:]


def main():
    if not TARGET_FILE.exists():
        print(f"error: {TARGET_FILE} does not exist", file=sys.stderr)
        sys.exit(1)

    folders = find_theme_folders()
    generated_body = render_sections(folders)

    original = TARGET_FILE.read_text(encoding="utf-8")
    updated = splice(original, generated_body)
    TARGET_FILE.write_text(updated, encoding="utf-8")

    total_files = sum(len(f["files"]) for f in folders)
    print(f"spliced {TARGET_FILE} ({len(folders)} theme folders, {total_files} json files)")


if __name__ == "__main__":
    main()
