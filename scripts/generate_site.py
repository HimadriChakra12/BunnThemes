#!/usr/bin/env python3
"""
generate_site.py

Walks the repository, finds every top-level "theme folder" that contains
one or more *.json theme files, and renders a static index.html listing
them in the form:

    ~/<Theme Folder>          (heading, level 5)
        ./<theme>.json        (clickable row)

Clicking a row copies the raw GitHub URL to the clipboard AND opens the
raw file in a new tab.

Usage: python3 scripts/generate_site.py
Output: site/index.html
"""

import json
import os
from pathlib import Path
from html import escape

# ---- config ---------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "site"
OUTPUT_FILE = OUTPUT_DIR / "index.html"

# Folders at repo root that are NOT theme folders
IGNORE_DIRS = {
    "Asset", ".github", ".git", "scripts", "site", "node_modules",
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


# ---- render html ------------------------------------------------------------

def render(folders):
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

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BunnThemes</title>
<style>
  :root {{
    --bg0: #1d2021;
    --bg1: #282828;
    --bg2: #3c3836;
    --fg0: #fbf1c7;
    --fg1: #ebdbb2;
    --fg-muted: #928374;
    --accent: #d79921;
    --accent-dim: #b16286;
    --mono: "JetBrains Mono", "Fira Code", ui-monospace, SFMono-Regular, Consolas, monospace;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 2.5rem 1.25rem 5rem;
    background: var(--bg0);
    color: var(--fg1);
    font-family: var(--mono);
    line-height: 1.5;
  }}
  header {{
    max-width: 720px;
    margin: 0 auto 2.5rem;
  }}
  header h1 {{
    margin: 0 0 0.35rem;
    color: var(--fg0);
    font-size: 1.4rem;
    letter-spacing: 0.02em;
  }}
  header p {{
    margin: 0;
    color: var(--fg-muted);
    font-size: 0.85rem;
  }}
  main {{
    max-width: 720px;
    margin: 0 auto;
  }}
  .theme-block {{
    margin-bottom: 1.75rem;
  }}
  .theme-heading {{
    margin: 0 0 0.5rem;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--accent);
  }}
  .file-list {{
    list-style: none;
    margin: 0;
    padding: 0;
    border: 1px solid var(--bg2);
    border-radius: 6px;
    overflow: hidden;
  }}
  .file-row {{
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    padding: 0.5rem 0.85rem;
    cursor: pointer;
    background: var(--bg1);
    border-bottom: 1px solid var(--bg2);
    position: relative;
    transition: background 0.12s ease;
  }}
  .file-row:last-child {{ border-bottom: none; }}
  .file-row:hover, .file-row:focus {{
    background: var(--bg2);
    outline: none;
  }}
  .file-row:active {{
    background: #4a4238;
  }}
  .file-path {{
    color: var(--fg-muted);
    font-size: 0.82rem;
  }}
  .file-name {{
    color: var(--fg1);
    font-size: 0.85rem;
  }}
  .copied-tag {{
    position: absolute;
    right: 0.85rem;
    top: 50%;
    transform: translateY(-50%) translateX(6px);
    font-size: 0.72rem;
    color: var(--bg0);
    background: var(--accent);
    padding: 0.1rem 0.45rem;
    border-radius: 4px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease, transform 0.15s ease;
  }}
  .file-row.copied .copied-tag {{
    opacity: 1;
    transform: translateY(-50%) translateX(0);
  }}
  footer {{
    max-width: 720px;
    margin: 3rem auto 0;
    color: var(--fg-muted);
    font-size: 0.75rem;
    text-align: center;
  }}
  footer a {{ color: var(--accent-dim); }}
</style>
</head>
<body>
<header>
  <h1>BunnThemes</h1>
  <p>click a file to copy its raw URL and open it</p>
</header>
<main>
{body}
</main>
<footer>
  auto-generated by <a href="{BLOB_BASE}/scripts/generate_site.py">generate_site.py</a> &middot;
  <a href="https://github.com/{GITHUB_USER}/{REPO_NAME}">source</a>
</footer>
<script>
  function copyUrl(url) {{
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(url).catch(function () {{
        fallbackCopy(url);
      }});
    }} else {{
      fallbackCopy(url);
    }}
  }}

  function fallbackCopy(url) {{
    var ta = document.createElement("textarea");
    ta.value = url;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {{ document.execCommand("copy"); }} catch (e) {{}}
    document.body.removeChild(ta);
  }}

  function openFile(url) {{
    window.open(url, "_blank", "noopener");
  }}

  document.querySelectorAll(".file-row").forEach(function (row) {{
    function trigger() {{
      var rawUrl = row.getAttribute("data-raw");
      var blobUrl = row.getAttribute("data-blob");
      copyUrl(rawUrl);
      openFile(blobUrl);
      row.classList.add("copied");
      setTimeout(function () {{ row.classList.remove("copied"); }}, 1200);
    }}
    row.addEventListener("click", trigger);
    row.addEventListener("keydown", function (e) {{
      if (e.key === "Enter" || e.key === " ") {{
        e.preventDefault();
        trigger();
      }}
    }});
  }});
</script>
</body>
</html>
"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    folders = find_theme_folders()
    html = render(folders)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    total_files = sum(len(f["files"]) for f in folders)
    print(f"wrote {OUTPUT_FILE} ({len(folders)} theme folders, {total_files} json files)")


if __name__ == "__main__":
    main()
