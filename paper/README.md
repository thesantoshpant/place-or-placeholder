# Paper 1 preprint draft: "Place or Placeholder?"

Current title: **Place or placeholder? AlphaEarth satellite embeddings did not detectably improve weekly dengue forecasts in four countries**. The current source is `paper/v1/` (Markdown), built with `scripts/paper/build_pdf.sh` and `scripts/paper/build_docx.sh`. The LaTeX file `main.tex` described below is the superseded v0 draft.

Build: `cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main` (or `latexmk -pdf main.tex`); arXiv-ready, standard TeX Live packages only.
Red `\todo{...}` marks pending results or decisions (Brazil S1 L3/L4/C* runs, all estimands, other countries, spatial splits, outbreak/lag/monthly analyses, freeze date, repo URL); orange `\citeneeded{...}` marks claims awaiting a verified reference.
Every number in the text comes from `docs/` (data, features, methods, results); `refs.bib` holds only references verified in `docs/research/`.
