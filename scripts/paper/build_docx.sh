#!/usr/bin/env bash
# Build one .docx of the paper draft (main text, reference list, supplements) for author review.
#
# Usage (on the GPU server, from the repo root):
#   source env.sh
#   bash scripts/paper/build_docx.sh [EXTRA_MD]
#
#   EXTRA_MD (optional): a markdown file that replaces the [[AI-USE: ...]] marker. If the file starts
#     with a heading and the marker sits directly under a heading, that heading is replaced too.
#     Without it the marker stays visible (bold), like every other [[...]] marker.
#
# Environment overrides: PAPER_DIR (default paper/v1), OUT_DIR (default tmp/gdoc_build),
#   BIB (default: the first *.bib in PAPER_DIR), MAX_W_IN / MAX_H_IN (image box, default 6.5 x 8.0 in).
#
# What it does (the source files are never edited; everything happens in a build copy):
#   - main text = PAPER_DIR/[0-9][0-9]_*.md in name order; then the reference list; then each
#     PAPER_DIR/S[0-9]*_*.md supplement after a page break;
#   - HTML comments are dropped; a "FIGURE <n> SPEC (to be drawn)" comment becomes a visible
#     placeholder with the spec as a bullet list;
#   - ```latex fences become display equations (a line holding only \qquad splits one into two,
#     so wide pairs do not overflow the page);
#   - [[...]] markers are kept and set in bold;
#   - each figure caption "**Figure <id>. ...** (`path.png`)" gets its image inserted right before it;
#     captions of main-text figures (numeric ids) that live in a supplement are moved into the main
#     text: after the figure's spec placeholder if there is one, else at the end of the subsection
#     that first cites the figure;
#   - citations via pandoc --citeproc (default author-date style).
# Output: $OUT_DIR/place_or_placeholder_<basename PAPER_DIR>.docx, plus the build copy build.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${VIRTUAL_ENV:-}" ]; then source env.sh; fi

PAPER_DIR="${PAPER_DIR:-paper/v1}"
OUT_DIR="${OUT_DIR:-tmp/gdoc_build}"
BIB="${BIB:-$(ls "$PAPER_DIR"/*.bib | head -n 1)}"
EXTRA_MD="${1:-}"
export MAX_W_IN="${MAX_W_IN:-6.5}" MAX_H_IN="${MAX_H_IN:-8.0}"
mkdir -p "$OUT_DIR"
BUILD_MD="$OUT_DIR/build.md"
OUT_DOCX="$OUT_DIR/place_or_placeholder_$(basename "$PAPER_DIR").docx"

python - "$PAPER_DIR" "$BUILD_MD" "$EXTRA_MD" <<'PY'
import os
import pathlib
import re
import sys

from PIL import Image

paper = pathlib.Path(sys.argv[1])
build_md = pathlib.Path(sys.argv[2])
extra_path = sys.argv[3]
root = pathlib.Path.cwd()
max_w, max_h = float(os.environ["MAX_W_IN"]), float(os.environ["MAX_H_IN"])

main_files = sorted(paper.glob("[0-9][0-9]_*.md"))
supp_files = sorted(paper.glob("S[0-9]*_*.md"))
if not main_files:
    sys.exit(f"no main-text files in {paper}")

CMT = r"<!--(?:(?!-->).)*-->"
PAGEBREAK = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'


def esc(s):
    return s.replace("*", r"\*")


def spec_block(num, body):
    """Turn a figure-spec comment into a visible placeholder plus a nested bullet list."""
    m = re.search(r'Title:\s*"([^"]+)"', body)
    title = m.group(1) if m else "untitled"
    head = f"**Figure {num} ({title[0].lower() + title[1:]}): to be drawn.** Drawing specification:"
    items = []
    for para in re.split(r"\n\s*\n", body.strip()):
        for line in para.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("- "):
                items.append("    - " + esc(line[2:]))
            else:
                items.append("- " + esc(line))
    return head + "\n\n" + "\n".join(items) + f"\n\n@@FIGCAP:{num}@@\n"


def latex_block(m):
    """A ```latex fence becomes display equations; a line holding only \\qquad starts a new one."""
    parts = [p.strip() for p in re.split(r"(?m)^[ \t]*\\qquad[ \t]*$", m.group(1)) if p.strip()]
    return "\n\n".join("$$\n" + p + "\n$$" for p in parts)


def preprocess(text):
    text = re.sub(r"(?s)<!--\s*FIGURE (\d+) SPEC \(to be drawn\)\.?\s*((?:(?!-->).)*)-->",
                  lambda m: spec_block(m.group(1), m.group(2)), text)
    text = re.sub(r"(?ms)^```latex[ \t]*\n(.*?)\n```[ \t]*$", latex_block, text)
    text = re.sub(r"(?ms)^[ \t]*" + CMT + r"[ \t]*\n", "", text)   # whole-line comments
    text = re.sub(r"(?s)[ \t]*" + CMT, "", text)                    # inline comments
    text = re.sub(r"\[\[(?!AI-USE)[A-Z][A-Z0-9 _-]*:[^\]]*\]\]", lambda m: "**" + m.group(0) + "**", text)
    return text


def insert_extra(text, extra):
    m = re.search(r"\[\[AI-USE:[^\]]*\]\]", text)
    if not m:
        return text, False
    if not extra:
        return text[:m.start()] + "**" + m.group(0) + "**" + text[m.end():], True
    before = text[:m.start()].rstrip("\n")
    last_nl = before.rfind("\n")
    prev_line = before[last_nl + 1:]
    hm = re.match(r"(#+) ", prev_line)
    em = re.match(r"(#+) (.*)\n", extra)
    if hm and em:
        extra = hm.group(1) + " " + em.group(2) + "\n" + extra[em.end():]
        return before[:last_nl + 1] + extra.strip() + text[m.end():], True
    return text[:m.start()] + extra.strip() + text[m.end():], True


def image_md(path):
    p = (root / path).resolve()
    if not p.is_file():
        sys.exit(f"figure file missing: {path}")
    with Image.open(p) as im:
        wpx, hpx = im.size
        dpi = (im.info.get("dpi") or (150, 150))[0] or 150
    w_in, h_in = wpx / dpi, hpx / dpi
    scale = min(1.0, max_w / w_in, max_h / h_in)
    return f"![]({p}){{width={w_in * scale:.2f}in}}"


extra = preprocess(pathlib.Path(extra_path).read_text()) if extra_path else ""
mains = [preprocess(f.read_text()) for f in main_files]
supps = [preprocess(f.read_text()) for f in supp_files]
placed_extra = False
for lst in (mains, supps):
    for i, t in enumerate(lst):
        lst[i], done = insert_extra(t, extra)
        placed_extra = placed_extra or done
if extra and not placed_extra:
    sys.exit("EXTRA_MD given but no [[AI-USE: ...]] marker found")

CAP = re.compile(r"(?ms)^\*\*Figure (\d+|S\d+-\d+)\. .*?(?=\n[ \t]*\n|\Z)")
PATH = re.compile(r"\s*\(`([^`]+\.(?:png|jpg|jpeg))`\)")


def fig_block(cap):
    pm = PATH.search(cap)
    if not pm:
        return cap
    return image_md(pm.group(1)) + "\n\n" + PATH.sub("", cap, count=1)


def cite_anchor(num):
    """(file index, offset) just before the heading that follows the first main-text citation."""
    cite = re.compile(rf"\bFig(?:ure|s?\.)?\s+{num}(?!\d)")
    for i, t in enumerate(mains):
        for m in cite.finditer(t):
            if t[:m.start()].rfind("\n**Figure ") > t[:m.start()].rfind("\n\n"):
                continue  # inside a caption
            h = re.search(r"(?m)^#+ ", t[m.end():])
            return i, (m.end() + h.start()) if h else len(t)
    return None


moved = []
for k, t in enumerate(supps):
    def repl(m):
        cap = m.group(0)
        num = m.group(1)
        if num.isdigit():
            moved.append((num, fig_block(cap)))
            return ""
        return fig_block(cap)
    supps[k] = re.sub(r"\n{3,}", "\n\n", CAP.sub(repl, t))
for i, t in enumerate(mains):
    mains[i] = CAP.sub(lambda m: fig_block(m.group(0)), t)
for num, block in moved:
    tok = f"@@FIGCAP:{num}@@"
    hit = [i for i, t in enumerate(mains) if tok in t]
    if hit:
        mains[hit[0]] = mains[hit[0]].replace(tok, block)
        continue
    anchor = cite_anchor(num)
    if anchor is None:
        sys.exit(f"Figure {num}: no spec placeholder and no citation in the main text")
    i, pos = anchor
    mains[i] = mains[i][:pos].rstrip("\n") + "\n\n" + block + "\n\n" + mains[i][pos:]
mains = [re.sub(r"@@FIGCAP:\d+@@\n?", "", t) for t in mains]

parts = [t.strip() for t in mains] + ["## References", "::: {#refs}\n:::"]
for t in supps:
    parts += [PAGEBREAK, t.strip()]
build_md.write_text("\n\n".join(parts) + "\n")
left = re.findall(r"<!--|-->|@@FIGCAP", build_md.read_text())
if left:
    sys.exit(f"leftover comment/token markers in build copy: {left[:5]}")
print(f"build copy: {build_md} ({len(mains)} main files, {len(supps)} supplements, "
      f"{len(moved)} main-text figure captions moved)")
PY

PANDOC="$(python -c 'import pypandoc; print(pypandoc.get_pandoc_path())')"
"$PANDOC" "$BUILD_MD" --from markdown --to docx --citeproc --bibliography "$BIB" \
  --resource-path . -o "$OUT_DOCX" 2> "$OUT_DIR/pandoc.log" || { cat "$OUT_DIR/pandoc.log" >&2; exit 1; }
if [ -s "$OUT_DIR/pandoc.log" ]; then echo "pandoc warnings (see $OUT_DIR/pandoc.log):"; head -n 20 "$OUT_DIR/pandoc.log"; fi
echo "wrote $OUT_DOCX"
