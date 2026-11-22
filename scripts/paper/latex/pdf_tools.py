#!/usr/bin/env python3
"""Helpers for scripts/paper/build_pdf.sh (run from the repo root, inside the venv).

    python scripts/paper/latex/pdf_tools.py prepare WORK PAPER_DIR AI_USE_MD
        Run the markdown preprocessing of scripts/paper/build_docx.sh (extracted from its heredoc at
        run time, so both builds share one source of truth) into WORK/build.md, with one change:
        aligned equation blocks stay whole (LaTeX typesets them; Word needed one display per row).
        Then split build.md into WORK/main.md (title page, abstract, main text, declarations,
        references) and WORK/supplement.md (title page, contents, S1, S2, own reference list).
    python scripts/paper/latex/pdf_tools.py check WORK OUT_DIR BIB CSL
        Counts, leftover-marker grep, log warnings and a numeric-token comparison of each PDF against
        the pandoc plain-text rendering of the same markdown. Writes OUT_DIR/CHECKS.md.
    python scripts/paper/latex/pdf_tools.py render PDF OUTDIR PAGES [DPI]
        Render pages (1-based, comma list or a-b ranges) to PNG for visual checks.
"""
import collections
import os
import pathlib
import re
import subprocess
import sys

PAGEBREAK = "§§PAGEBREAK§§"
ROOT = pathlib.Path.cwd()


def extract_preprocessor(dst):
    src = (ROOT / "scripts/paper/build_docx.sh").read_text()
    m = re.search(r"<<'PY'\n(.*?)\nPY\n", src, re.S)
    if not m:
        sys.exit("could not find the python heredoc in scripts/paper/build_docx.sh")
    code = m.group(1)
    old = "    text = ALIGNED.sub(unalign, text)\n"
    if code.count(old) != 1:
        sys.exit("build_docx.sh changed: the aligned-equation step was not found exactly once")
    code = code.replace(old, "    pass  # PDF build: aligned blocks stay whole\n")
    dst.write_text(code)


def prepare(work, paper_dir, ai_use):
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    pre = work / "docx_preprocess.py"
    extract_preprocessor(pre)
    env = dict(os.environ, MAX_W_IN=os.environ.get("MAX_W_IN", "6.5"), MAX_H_IN=os.environ.get("MAX_H_IN", "8.0"))
    build_md = work / "build.md"
    subprocess.run([sys.executable, str(pre), paper_dir, str(build_md), ai_use], check=True, env=env)
    text = build_md.read_text()

    m = re.search(r'(?m)^::: \{custom-style="Title"\}\nSupplementary Information for:', text)
    if not m:
        sys.exit("no 'Supplementary Information for:' title in build.md")
    main, supp = text[:m.start()], text[m.start():]
    main = re.sub(r"\s*" + PAGEBREAK + r"\s*$", "\n", main)
    # title page on its own: page break before the abstract heading
    main, k = re.subn(r"(?m)^# Abstract[ \t]*$", PAGEBREAK + "\n\n# Abstract", main, count=1)
    if k != 1:
        sys.exit("no '# Abstract' heading in the main text")

    # supplement front: keep the Title and Authors divs; the Contents list becomes \tableofcontents
    first_break = supp.index(PAGEBREAK)
    head, body = supp[:first_break], supp[first_break:]
    divs = re.findall(r'(?ms)^::: \{custom-style="([^"]+)"\}\n(.*?)\n:::[ \t]*$', head)
    keep = [f'::: {{custom-style="{s}"}}\n{t}\n:::' for s, t in divs if s in ("Title", "Authors")]
    toc = "```{=latex}\n\\vspace{10pt}\n{\\small\\tableofcontents}\n```"
    supp = "\n\n".join(keep + [toc]) + "\n\n" + body.strip() + "\n"
    if re.search(r"\[[^\]]*@[A-Za-z0-9_]", body) or re.search(r"(?<![\w@])@[A-Za-z][\w:-]*\d", body):
        supp += "\n\n# References\n\n::: {#refs}\n:::\n"
    (work / "main.md").write_text(main.strip() + "\n")
    (work / "supplement.md").write_text(supp)
    title = re.search(r'(?ms)^::: \{custom-style="Title"\}\n(.*?)\n:::', main).group(1).strip()
    authors = re.search(r'(?ms)^::: \{custom-style="Authors"\}\n(.*?)\n:::', main).group(1)
    authors = re.sub(r"\^\d+(,\d+)*\^", "", authors).strip()
    short = title.split("?")[0] + "?" if "?" in title else title
    for part, right in (("main", ""), ("supplement", "Supplementary Information")):
        (work / f"{part}.meta.yaml").write_text(
            "pdfpart: " + part + "\n"
            + "pdftitle: " + yq(title if part == "main" else "Supplementary Information for: " + title) + "\n"
            + "pdfauthor: " + yq(authors) + "\n"
            + "runninghead: " + yq(short) + "\n"
            + "runningright: " + yq(right) + "\n")
    print(f"prepared {work}/main.md ({len(main)} chars) and {work}/supplement.md ({len(supp)} chars)")


def yq(s):
    return "'" + s.replace("'", "''") + "'"


# ---------------------------------------------------------------------------------- checks
SUPMAP = str.maketrans({"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7",
                        "⁸": "8", "⁹": "9", "⁻": "−"})
NUM = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text):
    text = text.translate(SUPMAP)
    return collections.Counter(NUM.findall(text))


def pdf_text(pdf, doc_fonts_only=False):
    """Page texts. With doc_fonts_only, drop spans set in DejaVu (the matplotlib font of the
    embedded vector figures), so only document text is compared, and drop the page-number line."""
    import pymupdf
    doc = pymupdf.open(pdf)
    if not doc_fonts_only:
        return [p.get_text("text") for p in doc]
    pages = []
    for k, page in enumerate(doc, start=1):
        lines = []
        for b in page.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t, x1 = "", None
                for sp in ln["spans"]:
                    if "DejaVu" in sp["font"]:   # matplotlib text inside the vector figures
                        continue
                    gap = (sp["bbox"][0] - x1) if x1 is not None else 0
                    t += (" " if t and gap > 1.0 else "") + sp["text"]
                    x1 = sp["bbox"][2]
                if t.strip():
                    lines.append(t)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == str(k):
                del lines[i]
                break
        pages.append("\n".join(lines))
    return pages


def plain_text(md, bib, csl):
    pandoc = __import__("pypandoc").get_pandoc_path()
    out = subprocess.run([pandoc, md, "--from", "markdown", "--to", "plain", "--wrap=none", "--citeproc",
                          "--bibliography", bib, "--csl", csl], check=True, capture_output=True, text=True)
    return out.stdout


def split_refs(text, marker):
    i = text.rfind(marker)
    return (text[:i], text[i:]) if i >= 0 else (text, "")


def check(work, out_dir, bib, csl):
    work, out_dir = pathlib.Path(work), pathlib.Path(out_dir)
    lines = ["# PDF build checks", ""]
    all_keys = set()
    for part in ("main", "supplement"):
        tex = (work / f"{part}.tex").read_text()
        log = (work / f"{part}.log").read_text(errors="replace") if (work / f"{part}.log").exists() else ""
        pages = pdf_text(work / f"{part}.pdf", doc_fonts_only=True)
        ptxt = "\n".join(pages)
        n_long = tex.count("\\begin{longtable}")
        n_tab = tex.count("\\begin{tabular}")
        n_fig = tex.count("\\includegraphics")
        n_eq = len(re.findall(r"\\tag\{", tex))
        n_disp = len(re.findall(r"(?<!\\)\\\[", tex))
        keys = re.findall(r"\\bibitem\[\\citeproctext\]\{ref-([^}]+)\}", tex)
        all_keys |= set(keys)
        lines += [f"## {part}", "",
                  f"- pages: {len(pages)}",
                  f"- tables: {n_long + n_tab} ({n_tab} float tabular, {n_long} longtable)",
                  f"- figures: {n_fig}",
                  f"- numbered equations: {n_eq}; unnumbered displays: {n_disp}",
                  f"- references in list: {len(keys)}"]
        # leftover markers
        bad = {}
        for pat in ("<!--", "[[", "PENDING", "Pending", "??", "@@", "§§"):
            hits = [m.start() for m in re.finditer(re.escape(pat), ptxt)]
            if hits:
                bad[pat] = [ptxt[max(0, h - 50):h + 50].replace("\n", " ") for h in hits[:6]]
        lines.append(f"- marker grep: {'none' if not bad else ''}")
        for pat, ctx in bad.items():
            lines.append(f"  - `{pat}` x{len(ctx)}: " + " | ".join(f"…{c}…" for c in ctx))
        # log warnings
        over = re.findall(r"Overfull \\hbox \(([\d.]+)pt too wide\)[^\n]*\n?([^\n]*)", log)
        big = [(float(w), ctx[:80]) for w, ctx in over if float(w) > 1.0]
        miss = sorted(set(re.findall(r"Missing character: There is no (\S+)", log)))
        undef = sorted(set(re.findall(r"(?:Hyper reference|Reference|Citation) `([^']+)' [^\n]*undefined", log)))
        lines.append(f"- overfull hboxes > 1pt: {len(big)}" + ("".join(f"\n  - {w:.1f}pt: {c}" for w, c in big[:15])))
        lines.append(f"- missing glyphs: {miss or 'none'}")
        lines.append(f"- undefined references: {undef or 'none'}")
        # numbers
        src = plain_text(str(work / f"{part}.md"), bib, csl)
        s_body, s_refs = split_refs(src, "\nReferences\n")
        p_body, p_refs = split_refs(ptxt, "\nReferences\n")
        ns, np_ = numbers(s_body), numbers(p_body)
        lost = {k: ns[k] - np_.get(k, 0) for k in ns if ns[k] > np_.get(k, 0)}
        extra = {k: np_[k] - ns.get(k, 0) for k in np_ if np_[k] > ns.get(k, 0)}
        lines.append(f"- numeric tokens, body (source {sum(ns.values())}, pdf {sum(np_.values())}): "
                     f"{sum(lost.values())} missing from the PDF, {sum(extra.values())} extra in the PDF")
        if lost:
            lines.append("  - missing: " + ", ".join(f"{k}×{v}" for k, v in sorted(lost.items())[:80]))
        if extra:
            lines.append("  - extra: " + ", ".join(f"{k}×{v}" for k, v in sorted(extra.items(), key=lambda kv: -kv[1])[:60]))
        ds = re.sub(r"\D", "", s_refs.translate(SUPMAP))
        dp = re.sub(r"\D", "", p_refs.translate(SUPMAP))
        # page numbers sit between reference lines in the PDF: compare after removing them is not
        # reliable, so test containment of the source digit stream with page numbers stripped per page
        lines.append(f"- reference-list digits identical to source: {ds == dp} "
                     f"(source {len(ds)} digits, pdf {len(dp)})")
        (work / f"{part}.plain.txt").write_text(src)
        (work / f"{part}.pdftext.txt").write_text("\n\f\n".join(pages))
        lines.append("")
    lines.append(f"Distinct references over both lists: {len(all_keys)}")
    (out_dir / "CHECKS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def render(pdf, outdir, pages, dpi=110):
    import pymupdf
    doc = pymupdf.open(pdf)
    outdir = pathlib.Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    want = []
    for tok in pages.split(","):
        if "-" in tok:
            a, b = tok.split("-")
            want += list(range(int(a), int(b) + 1))
        elif tok:
            want.append(int(tok))
    stem = pathlib.Path(pdf).stem
    for p in want:
        if 1 <= p <= len(doc):
            pix = doc[p - 1].get_pixmap(dpi=int(dpi))
            f = outdir / f"{stem}_p{p:03d}.png"
            pix.save(f)
            print(f)


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    if cmd == "prepare":
        prepare(*args)
    elif cmd == "check":
        check(*args)
    elif cmd == "render":
        render(*args)
    else:
        sys.exit(__doc__)
