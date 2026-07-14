#!/usr/bin/env python3
"""
Preprocess chapters for EPUB build.

Reads mkdocs.yml nav, emits:
  - Part heading files (part-01.md … part-10.md) in <outdir>
  - Preprocessed chapter files in <outdir>

Preprocessing per chapter:
  1. Replace <iframe> + "[open in a new tab](...)" block in "## Try It"
     with a static image + caption.
  2. Strip "Continue →" navigation links at the end.
  3. Leave everything else intact.

Also writes <outdir>/spine.txt — ordered list of markdown files for pandoc.

Usage:
    python3 preprocess_chapters.py <repo_root> <outdir>
"""

import re
import sys
import os

REPO = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

MKDOCS = os.path.join(REPO, "mkdocs.yml")
DOCS = os.path.join(REPO, "docs")

# ---------- parse mkdocs.yml nav (stdlib yaml-free, just enough) ----------

def parse_nav(path):
    """
    Returns list of (kind, label, filename) where kind is
    'part' | 'chapter' | 'skip'.
    """
    entries = []
    with open(path) as f:
        lines = f.readlines()

    in_nav = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.strip() == "nav:":
            in_nav = True
            continue
        if not in_nav:
            continue
        # stop at next top-level key (no leading spaces, ends with ':')
        if stripped and stripped[0] != " " and stripped.endswith(":"):
            break

        # detect indentation level
        content = stripped.lstrip()
        indent = len(stripped) - len(content)

        if not content.startswith("- "):
            continue
        content = content[2:]  # strip "- "

        if ":" in content:
            # Could be  "Label: file.md"  or  "Part N — Name:"
            colon_idx = content.index(":")
            label = content[:colon_idx].strip()
            value = content[colon_idx+1:].strip()
            if value == "":
                # Part heading
                entries.append(("part", label, None))
            else:
                # chapter entry
                entries.append(("chapter", label, value))
        # else: bare label (shouldn't happen in this nav)

    return entries


nav = parse_nav(MKDOCS)

# Chapters/pages to skip entirely
SKIP_LABELS = {"Home", "Philosophy", "Roadmap"}

# ---------- iframe → image replacement ----------

# Matches the <iframe> line
IFRAME_RE = re.compile(
    r'<iframe[^>]*src="[^"]*/(chapter\d+)/index\.html"[^>]*></iframe>',
    re.IGNORECASE,
)
# Matches the fallback link line
NEWTAB_RE = re.compile(
    r'^\[open in a new tab\]\([^)]+\)\s*$',
    re.IGNORECASE,
)

# Matches Continue → navigation line at end
CONTINUE_RE = re.compile(
    r'^\*\*Continue\s*[→>]\s*.*\*\*\s*$'
)

def chapter_title_from_h1(text):
    """Extract the H1 title from markdown text."""
    m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    return m.group(1).strip() if m else "Chapter"

def chapter_num_from_filename(fname):
    """e.g. '01-why-counting-exists.md' -> 'chapter01'"""
    m = re.match(r'^(\d+)-', os.path.basename(fname))
    if m:
        return "chapter" + m.group(1).zfill(2)
    return None

def preprocess(src_path, out_path):
    with open(src_path) as f:
        text = f.read()

    title = chapter_title_from_h1(text)
    chnum = chapter_num_from_filename(src_path)  # e.g. "chapter01"

    lines = text.splitlines(keepends=True)
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Strip Continue → lines (whole line)
        if CONTINUE_RE.match(line.rstrip()):
            # Also eat a preceding "---" separator if present
            if result and result[-1].strip() == "---":
                result.pop()
            i += 1
            continue

        # Detect iframe
        m = IFRAME_RE.search(line)
        if m:
            chn = m.group(1)  # e.g. "chapter01"
            # Build replacement
            img_line = f'![Simulation — {title}](assets/sim-screenshots/{chn}.png)\n'
            caption_line = f'*Interactive version: `browser/{chn}/index.html` in the repository — runs in any browser, nothing to install.*\n'
            result.append(img_line)
            result.append(caption_line)
            # Skip the next non-empty line if it's the "[open in a new tab]" link
            i += 1
            # skip blank line between iframe and link (if any)
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and NEWTAB_RE.match(lines[i].strip()):
                i += 1  # consume the link line
            continue

        # Regular line
        result.append(line)
        i += 1

    with open(out_path, "w") as f:
        f.writelines(result)


# ---------- write part headers ----------

PART_ROMAN = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10,
}

def part_file_name(label):
    """'Part I — Information' -> 'part-01.md'"""
    m = re.match(r'Part\s+([IVX]+)', label)
    if m:
        roman = m.group(1)
        n = PART_ROMAN.get(roman, 0)
        return f"part-{n:02d}.md"
    return "part-XX.md"


# ---------- build spine ----------

spine = []  # list of absolute paths

for kind, label, filename in nav:
    if label in SKIP_LABELS:
        continue

    if kind == "part":
        pfile = part_file_name(label)
        ppath = os.path.join(OUTDIR, pfile)
        with open(ppath, "w") as f:
            f.write(f"# {label}\n")
        spine.append(ppath)

    elif kind == "chapter":
        src = os.path.join(DOCS, filename)
        out_name = os.path.basename(filename)
        out_path = os.path.join(OUTDIR, out_name)
        preprocess(src, out_path)
        spine.append(out_path)

# Write spine
spine_path = os.path.join(OUTDIR, "spine.txt")
with open(spine_path, "w") as f:
    for p in spine:
        f.write(p + "\n")

processed = sum(1 for k, label, _ in nav if k == 'chapter' and label not in SKIP_LABELS)
parts = sum(1 for k, _, _ in nav if k == 'part')
print(f"Preprocessed {processed} chapters")
print(f"Parts: {parts}")
print(f"Spine written to {spine_path}")
