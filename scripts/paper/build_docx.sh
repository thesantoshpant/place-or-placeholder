#!/usr/bin/env bash
# Build one typeset .docx of the paper draft (main text, references, supplements) for author review
# in Google Docs (File > Open > Upload converts it to a native, editable Doc).
#
# Usage (on the GPU server, from the repo root):
#   source env.sh
#   bash scripts/paper/build_docx.sh [AI_USE_MD]
#
#   AI_USE_MD (optional; default tmp/ai_use_statement.md when it exists): a markdown paragraph that
#     replaces the AI-use marker ([[AI-USE: ...]] or <!-- AI-USE -->) under "Use of AI tools". If the
#     file starts with a heading and the marker sits directly under a heading, that heading is replaced.
#     Without it the marker stays visible as a grey placeholder.
#
# Environment overrides: PAPER_DIR (default paper/v1), OUT_DIR (default tmp/gdoc_build),
#   BIB (default: the first *.bib in PAPER_DIR), CSL (default scripts/paper/plos.csl),
#   MAX_W_IN / MAX_H_IN (image box, default 6.5 x 8.0 in).
#
# Steps (the source files are never edited; everything happens in a build copy):
#   1. build.md: main text = PAPER_DIR/[0-9][0-9]_*.md in name order, then References, then a
#      "Supplementary Information for: <title>" title page and each PAPER_DIR/S[0-9]*_*.md supplement
#      on a new page.
#        - HTML comments are dropped; a "FIGURE <n> SPEC (to be drawn)" comment becomes a visible
#          placeholder with the spec as a bullet list (dropped once a drawn figure exists);
#        - title page: title, authors, one paragraph per affiliation, corresponding-author lines;
#          a "Keywords:" paragraph (or "## Keywords" section) becomes a run-in "Keywords:" paragraph; a page break precedes "1 Introduction";
#        - main-text headings move up one level (sections = Heading 1, subsections = Heading 2);
#        - ```latex fences become display equations (a line holding only \qquad splits one into two,
#          and wide ",\quad"-separated lists are broken over lines so they fit the page); an
#          aligned block becomes one centred display per row, the equation number on the last row;
#        - [[...]] markers, [pending] and [to be completed] keep their text and get the grey
#          "Placeholder" character style (normal weight);
#        - each figure caption "**Figure <id>. ...**" gets its image inserted right before it, taken
#          ONLY from the drawn publication figures in docs/results/figures/pub/ (Fig<id>.png or
#          Fig<id>_*.png; FigS<k>.png also serves Figure S<n>-<k>); a figure without one stops the build
#          unless ALLOW_MISSING_FIGURES=1; captions of main-text figures (numeric ids) that live in a
#          supplement are moved into the main text: at the figure's spec placeholder if there is one,
#          else at the end of the subsection that first cites the figure;
#        - "Note: ..." paragraphs right after a table become 8.5 pt table notes; a table cell reading
#          "pending" (followed by a PENDING comment) gets the grey placeholder style;
#        - stand-alone horizontal rules (---) are dropped.
#   2. pandoc (bundled with pypandoc) -> docx with --citeproc, the PLOS CSL and scripts/paper/reference.docx.
#   3. scripts/paper/polish_docx.py: writes all formatting as direct formatting (fonts, spacing,
#      booktabs table rules, column widths, captions above tables with notes below, centred figures and
#      equations, hanging-indent references, page numbers), because Google Docs drops style-based
#      table borders and maps theme fonts badly.
#
# The PLOS style is plos.csl from github.com/citation-style-language/styles (master, fetched
# 2026-11-18, sha256 9e4e46b754097ccc48377aeeeccf28e1d58c3fac169a46cbc7ef8a5fad97c35f; CC BY-SA 3.0).
# Output: $OUT_DIR/place_or_placeholder_<basename PAPER_DIR>.docx, plus the build copy build.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
if [ -z "${VIRTUAL_ENV:-}" ]; then source env.sh; fi

PAPER_DIR="${PAPER_DIR:-paper/v1}"
OUT_DIR="${OUT_DIR:-tmp/gdoc_build}"
BIB="${BIB:-$(ls "$PAPER_DIR"/*.bib | head -n 1)}"
CSL="${CSL:-scripts/paper/plos.csl}"
REF_DOCX="scripts/paper/reference.docx"
POLISH="scripts/paper/polish_docx.py"
AI_USE_MD="${1:-}"
if [ -z "$AI_USE_MD" ] && [ -f tmp/ai_use_statement.md ]; then AI_USE_MD=tmp/ai_use_statement.md; fi
export MAX_W_IN="${MAX_W_IN:-6.5}" MAX_H_IN="${MAX_H_IN:-8.0}"
mkdir -p "$OUT_DIR"
BUILD_MD="$OUT_DIR/build.md"
RAW_DOCX="$OUT_DIR/pandoc_raw.docx"
OUT_DOCX="$OUT_DIR/place_or_placeholder_$(basename "$PAPER_DIR").docx"

python - "$PAPER_DIR" "$BUILD_MD" "$AI_USE_MD" <<'PY'
import os
import pathlib
import re
import sys

from PIL import Image

paper = pathlib.Path(sys.argv[1])
build_md = pathlib.Path(sys.argv[2])
extra_path = sys.argv[3]
root = pathlib.Path.cwd()
pub_dir = root / "docs/results/figures/pub"
max_w, max_h = float(os.environ["MAX_W_IN"]), float(os.environ["MAX_H_IN"])

main_files = sorted(paper.glob("[0-9][0-9]_*.md"))
supp_files = sorted(paper.glob("S[0-9]*_*.md"))
if not main_files:
    sys.exit(f"no main-text files in {paper}")

CMT = r"<!--(?:(?!-->).)*-->"
PAGEBREAK = "§§PAGEBREAK§§"   # replaced by a real page break in polish_docx.py
MARKER = r"\[\[(?!AI-USE)[A-Z][A-Z0-9 _/-]*:[^\]]*\]\]"


def esc(s):
    return s.replace("*", r"\*")


def div(style, text):
    return f'::: {{custom-style="{style}"}}\n{text}\n:::'


def pub_image(num):
    """A drawn figure in docs/results/figures/pub/ for figure id `num` (e.g. 2 or S2-1), if any."""
    if not pub_dir.is_dir():
        return None
    ids = [num]
    m = re.fullmatch(r"S\d+-(\d+)", num)      # Figure S2-1 is drawn as FigS1.png
    if m:
        ids.append("S" + m.group(1))
    for i in ids:
        for pat in (f"Fig{i}.png", f"Fig{i}_*.png", f"Fig{i}-*.png"):
            hits = sorted(pub_dir.glob(pat))
            if hits:
                return hits[0]
    return None


def spec_block(num, body):
    """Turn a figure-spec comment into a visible placeholder plus a nested bullet list."""
    if pub_image(num):
        return f"\n@@FIGCAP:{num}@@\n"
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


def visible_len(tex):
    t = re.sub(r"\\(mathrm|operatorname|text|left|right|big|Big)\b", "", tex)
    t = re.sub(r"\\[a-zA-Z]+", "x", t)
    return len(re.sub(r"[{}\s^_]", "", t))


def split_wide(tex, limit=60):
    """Break a wide ',\\quad'-separated list of equations into lines that fit the text width."""
    pieces = [p.strip() for p in re.split(r",\s*\\quad\s*", tex)]
    if len(pieces) == 1 or visible_len(tex) <= limit:
        return [tex]
    lines, cur = [], ""
    for p in pieces:
        cand = p if not cur else cur + r",\qquad " + p
        if cur and visible_len(cand) > limit:
            lines.append(cur)
            cur = p
        else:
            cur = cand
    lines.append(cur)
    return [ln + ("," if i < len(lines) - 1 else "") for i, ln in enumerate(lines)]


def latex_block(m):
    """A ```latex fence becomes display equations; a line holding only \\qquad starts a new one."""
    parts = [p.strip() for p in re.split(r"(?m)^[ \t]*\\qquad[ \t]*$", m.group(1)) if p.strip()]
    eqs = [e for p in parts for e in split_wide(p)]
    return "\n\n".join("$$\n" + e + "\n$$" for e in eqs)


ALIGNED = re.compile(r"\$\$\s*\\begin\{aligned\}(.*?)\\end\{aligned\}\s*(.*?)\s*\$\$", re.S)


def unalign(m):
    """$$\\begin{aligned} r1 \\\\ r2 \\end{aligned} \\qquad (n)$$ -> one centred display per row (number on
    the last row): Google Docs flattens aligned blocks (eqArr) onto one overflowing line."""
    rows = [r.strip() for r in re.split(r"\\\\", m.group(1)) if r.strip()]
    tail = m.group(2).strip()
    out = []
    for k, r in enumerate(rows):
        r = re.sub(r"&\s*=", "=", r)
        r = re.sub(r"\s*&\s*", r" \\qquad ", r).strip()
        if k == len(rows) - 1 and tail:
            r += " " + tail
        out.append("$$" + r + "$$")
    return "\n\n".join(out)


def placeholder(m):
    inner = re.sub(r"([\[\]*_\\`])", r"\\\1", m.group(0))
    return "[" + inner + ']{custom-style="Placeholder"}'


def preprocess(text):
    text = re.sub(r"<!--\s*AI-USE\s*-->", "[[AI-USE: statement]]", text)
    text = re.sub(r"(?<![\w\[])pending(?=[ \t]*<!--\s*PENDING)", placeholder, text)  # table-cell "pending"
    text = re.sub(r"(?s)<!--\s*FIGURE (\d+) SPEC \(to be drawn\)\.?\s*((?:(?!-->).)*)-->",
                  lambda m: spec_block(m.group(1), m.group(2)), text)
    text = re.sub(r"(?ms)^```latex[ \t]*\n(.*?)\n```[ \t]*$", latex_block, text)
    text = ALIGNED.sub(unalign, text)
    text = re.sub(r"(?ms)^[ \t]*" + CMT + r"[ \t]*\n", "", text)   # whole-line comments
    text = re.sub(r"(?s)[ \t]*" + CMT, "", text)                    # inline comments
    text = re.sub(r"(?m)(?<=\n\n)(?:---|\*\*\*|___)[ \t]*\n(?=\s*\n)", "", text)  # horizontal rules
    text = re.sub(MARKER, placeholder, text)
    text = re.sub(r"(?i)(?<![\[\\])\[(pending|to be completed)\](?![\[\({:])", placeholder, text)
    return text


def insert_extra(text, extra):
    m = re.search(r"\[\[AI-USE:[^\]]*\]\]", text)
    if not m:
        return text, False
    if not extra:
        return text[:m.start()] + placeholder(m) + text[m.end():], True
    before = text[:m.start()].rstrip("\n")
    last_nl = before.rfind("\n")
    prev_line = before[last_nl + 1:]
    hm = re.match(r"(#+) ", prev_line)
    em = re.match(r"(#+) (.*)\n", extra)
    if hm and em:
        extra = hm.group(1) + " " + em.group(2) + "\n" + extra[em.end():]
        return before[:last_nl + 1] + extra.strip() + text[m.end():], True
    return text[:m.start()] + extra.strip() + text[m.end():], True


def image_md(p):
    p = (root / p).resolve()
    if not p.is_file():
        sys.exit(f"figure file missing: {p}")
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
    sys.exit("AI-use statement given but no [[AI-USE: ...]] or <!-- AI-USE --> marker found")

CAP = re.compile(r"(?ms)^\*\*Figure (\d+|S\d+(?:-\d+)?)\. .*?(?=\n[ \t]*\n|\Z)")
PATH = re.compile(r"\s*\(`([^`]+\.(?:png|jpg|jpeg))`\)")
fig_log = []


def fig_block(cap, num):
    pm = PATH.search(cap)
    src = pub_image(num)
    if src is None and pm and "figures/pub/" in pm.group(1):
        src = pm.group(1)
    cap = PATH.sub("", cap, count=1)
    if src is None:   # only drawn publication figures are used, never the older kit PNGs
        if os.environ.get("ALLOW_MISSING_FIGURES"):
            fig_log.append(f"Figure {num}: NO publication figure in {pub_dir}")
            return cap
        sys.exit(f"Figure {num}: no publication figure in {pub_dir} (set ALLOW_MISSING_FIGURES=1 to build without it)")
    fig_log.append(f"Figure {num}: {os.path.relpath(root / src, root)}")
    return image_md(src) + "\n\n" + cap


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
        num = m.group(1)
        if num.isdigit():
            moved.append((num, fig_block(m.group(0), num)))
            return ""
        return fig_block(m.group(0), num)
    supps[k] = re.sub(r"\n{3,}", "\n\n", CAP.sub(repl, t))
for i, t in enumerate(mains):
    mains[i] = CAP.sub(lambda m: fig_block(m.group(0), m.group(1)), t)
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

# ---- title page -------------------------------------------------------------------------------
m = re.match(r"\s*# (.+)\n", mains[0])
if not m:
    sys.exit("00_front.md must start with '# <title>'")
title = m.group(1).strip()
rest = mains[0][m.end():]
h = re.search(r"(?m)^## ", rest)
block, body = (rest[:h.start()], rest[h.start():]) if h else (rest, "")
front = [div("Title", title)]
authors_line = ""
for k, para in enumerate(p for p in re.split(r"\n\s*\n", block.strip()) if p.strip()):
    for line in (ln.strip().rstrip("\\").rstrip() for ln in para.splitlines() if ln.strip()):
        if k == 0:
            style = "Authors"
            authors_line = authors_line or line
        elif re.match(r"\^\d+\^", line):
            style = "Affiliation"
        else:
            style = "Front Matter"
        front.append(div(style, line))
body = re.sub(r"(?ms)^## Keywords[ \t]*\n\s*\n(.+?)(?=\n[ \t]*\n|\Z)",
              lambda k: div("Keywords", "**Keywords:** " + k.group(1).strip()), body)
body = re.sub(r"(?ms)^Keywords:[ \t]*(.+?)(?=\n[ \t]*\n|\Z)",
              lambda k: div("Keywords", "**Keywords:** " + k.group(1).strip()), body)
mains[0] = "\n\n".join(front) + "\n\n" + body

# main-text headings move up one level: sections become Heading 1, subsections Heading 2
mains = [re.sub(r"(?m)^#(#+) ", r"\1 ", t) for t in mains]
main_text = "\n\n".join(t.strip() for t in mains)
first_sec = re.search(r"(?m)^# 1\.? ", main_text)
if first_sec:
    main_text = main_text[:first_sec.start()] + PAGEBREAK + "\n\n" + main_text[first_sec.start():]

parts = [main_text, "# References", "::: {#refs}\n:::"]
if supps:
    supp_titles = [re.search(r"(?m)^# (.+)$", t).group(1).strip() for t in supps]
    parts += [PAGEBREAK, div("Title", f"Supplementary Information for: {title}")]
    if authors_line:
        parts.append(div("Authors", authors_line))
    parts.append(div("Front Matter", "**Contents**"))
    parts += [div("Front Matter", s) for s in supp_titles]
    for t in supps:
        parts += [PAGEBREAK, t.strip()]
build_md.write_text("\n\n".join(parts) + "\n")
left = re.findall(r"<!--|-->|@@FIGCAP", build_md.read_text())
if left:
    sys.exit(f"leftover comment/token markers in build copy: {left[:5]}")
print(f"build copy: {build_md} ({len(main_files)} main files, {len(supps)} supplements, "
      f"{len(moved)} main-text figure captions moved)")
for line in fig_log:
    print("  " + line)
PY

PANDOC="$(python -c 'import pypandoc; print(pypandoc.get_pandoc_path())')"
if [ ! -f "$REF_DOCX" ] || [ "$POLISH" -nt "$REF_DOCX" ]; then
  python "$POLISH" reference "$REF_DOCX" "$PANDOC"
fi
"$PANDOC" "$BUILD_MD" --from markdown --to docx --citeproc --bibliography "$BIB" --csl "$CSL" \
  --reference-doc "$REF_DOCX" --resource-path . -o "$RAW_DOCX" 2> "$OUT_DIR/pandoc.log" \
  || { cat "$OUT_DIR/pandoc.log" >&2; exit 1; }
if [ -s "$OUT_DIR/pandoc.log" ]; then echo "pandoc warnings (see $OUT_DIR/pandoc.log):"; head -n 20 "$OUT_DIR/pandoc.log"; fi
python "$POLISH" polish "$RAW_DOCX" "$OUT_DOCX"
echo "wrote $OUT_DOCX"
