#!/usr/bin/env bash
# Build the two medRxiv PDFs of the paper (manuscript and supplement) with pandoc + Tectonic (XeTeX).
#
# Usage (on the GPU server, from anywhere inside the repo):
#   bash scripts/paper/build_pdf.sh [AI_USE_MD]
#
# AI_USE_MD (optional; default tmp/ai_use_statement.md when it exists) replaces the AI-use marker under
# "Use of AI tools", exactly as in scripts/paper/build_docx.sh. The statement stays outside the repo.
#
# Steps:
#   1. scripts/paper/latex/pdf_tools.py prepare: runs the markdown preprocessing of build_docx.sh
#      (its python heredoc, extracted at run time, so content matches the Word build) into
#      $WORK/build.md, keeping aligned equations whole, and splits it into main.md and supplement.md.
#   2. pandoc (pypandoc binary) -> LaTeX with --citeproc (PLOS CSL), the template
#      scripts/paper/latex/template.tex and the filter scripts/paper/latex/pdf_filter.lua.
#   3. Tectonic compiles each .tex (bundle cache in .cache/tectonic).
#   4. pdf_tools.py check: counts, marker grep, log warnings, numeric-token comparison -> CHECKS.md.
#
# Environment overrides: PAPER_DIR (paper/v1), OUT_DIR (tmp/pdf_build), BIB (first *.bib in PAPER_DIR),
#   CSL (scripts/paper/plos.csl), TECTONIC (.tools/bin/tectonic).
# Outputs: $OUT_DIR/place_or_placeholder_main.pdf, $OUT_DIR/place_or_placeholder_supplement.pdf.
set -euo pipefail
cd "$(dirname "$0")/../.."
ROOT="$PWD"
if [ -z "${VIRTUAL_ENV:-}" ]; then source env.sh; fi
export TECTONIC_CACHE_DIR="$ROOT/.cache/tectonic"
mkdir -p "$TECTONIC_CACHE_DIR"

PAPER_DIR="${PAPER_DIR:-paper/v1}"
OUT_DIR="${OUT_DIR:-tmp/pdf_build}"
WORK="$OUT_DIR/work"
BIB="${BIB:-$(ls "$PAPER_DIR"/*.bib | head -n 1)}"
CSL="${CSL:-scripts/paper/plos.csl}"
TECTONIC="${TECTONIC:-$ROOT/.tools/bin/tectonic}"
LATEX_DIR="scripts/paper/latex"
AI_USE_MD="${1:-}"
if [ -z "$AI_USE_MD" ] && [ -f tmp/ai_use_statement.md ]; then AI_USE_MD=tmp/ai_use_statement.md; fi
mkdir -p "$WORK"

python "$LATEX_DIR/pdf_tools.py" prepare "$WORK" "$PAPER_DIR" "$AI_USE_MD"

PANDOC="$(python -c 'import pypandoc; print(pypandoc.get_pandoc_path())')"
for part in main supplement; do
  "$PANDOC" "$WORK/$part.md" --from markdown --to latex --standalone \
    --template "$LATEX_DIR/template.tex" --metadata-file "$WORK/$part.meta.yaml" \
    --citeproc --bibliography "$BIB" --csl "$CSL" -M link-citations=true -M link-bibliography=true \
    --lua-filter "$LATEX_DIR/pdf_filter.lua" -o "$WORK/$part.tex" 2> "$WORK/$part.pandoc.log" \
    || { cat "$WORK/$part.pandoc.log" >&2; exit 1; }
  grep 'WARNING\|^\[' "$WORK/$part.pandoc.log" || true   # full table/figure log in $WORK/$part.pandoc.log
  (cd "$WORK" && nice -n 19 "$TECTONIC" -X compile --keep-logs "$part.tex" > "$part.tectonic.log" 2>&1) \
    || { tail -n 40 "$WORK/$part.tectonic.log" >&2; exit 1; }
  cp "$WORK/$part.pdf" "$OUT_DIR/place_or_placeholder_$part.pdf"
  echo "wrote $OUT_DIR/place_or_placeholder_$part.pdf"
done

python "$LATEX_DIR/pdf_tools.py" check "$WORK" "$OUT_DIR" "$BIB" "$CSL" > /dev/null
echo "checks: $OUT_DIR/CHECKS.md"
