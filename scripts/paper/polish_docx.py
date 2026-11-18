#!/usr/bin/env python3
"""Typeset a pandoc-built .docx of the paper as a journal manuscript that survives Google Docs import.

    python scripts/paper/polish_docx.py reference OUT.docx [PANDOC]   write the pandoc reference doc
    python scripts/paper/polish_docx.py polish IN.docx OUT.docx         restyle a pandoc build
    python scripts/paper/polish_docx.py inspect DOCX                    print a structural summary

Google Docs keeps direct formatting but drops style-based table borders and maps theme fonts badly,
so `polish` writes every font, size, spacing, alignment, table rule and column width as direct
formatting with explicit (non-theme) fonts. The same STYLES table defines the named styles of the
reference document, so Word shows the same layout.

Layout: US Letter, 1 in margins (6.5 in text width); body 11 pt Times New Roman, 1.15 lines, 6 pt
after; headings Arial bold 14/12/11 pt; title 18 pt; tables in booktabs style (1 pt top and bottom
rules, 0.5 pt rule under the header, no vertical lines), Arial 9 pt (8.5/8 pt for wide tables),
numeric columns right-aligned, widths fitted to the content and summing to the text width; caption
"Table N. Title." above the table; a legend run on after the title, or a "Note:" paragraph
after the table, set below the table as an 8.5 pt note; figures
and display equations centred; figure captions 9.5 pt below; references with a hanging indent;
grey placeholders; centred page numbers in the footer.
"""
import copy
import re
import subprocess
import sys

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from lxml import etree

SERIF, SANS, MONO = "Times New Roman", "Arial", "Courier New"
TEXT_W = 9360            # text width, 6.5 in, in dxa (1/20 pt)
GREY = "E6E6E6"          # placeholder shading
CELL_LR, CELL_TB = 72, 20  # cell padding (dxa): 0.05 in left/right, 1 pt top/bottom
RULE_HEAVY, RULE_LIGHT = 8, 4  # border sizes in 1/8 pt: 1 pt and 0.5 pt
PAGEBREAK = "§§PAGEBREAK§§"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

RPR_ORDER = ("rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint "
             "noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u "
             "effect bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath").split()
PPR_ORDER = ("pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers "
             "pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE "
             "autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents "
             "suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle "
             "rPr sectPr pPrChange").split()
TBLPR_ORDER = ("tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc "
               "tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption "
               "tblDescription").split()
TCPR_ORDER = ("cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText "
              "vAlign hideMark").split()


def S(font=SERIF, size=11.0, bold=None, italic=None, before=0, after=6, line=1.15, align="left",
      keep=False, left=0.0, hanging=0.0):
    return dict(font=font, size=size, bold=bold, italic=italic, before=before, after=after,
                line=line, align=align, keep=keep, left=left, hanging=hanging)


PARA = {
    "Normal": S(),
    "Body Text": S(),
    "First Paragraph": S(),
    "Compact": S(after=2),
    "Title": S(SANS, 18, True, before=0, after=14, line=1.1, keep=True),
    "Subtitle": S(SANS, 13, after=10),
    "Authors": S(size=11.5, after=8),
    "Affiliation": S(size=9.5, after=0, line=1.1),
    "Front Matter": S(size=9.5, before=4, after=0, line=1.1),
    "Keywords": S(before=6, after=6),
    "Heading 1": S(SANS, 14, True, before=18, after=6, line=1.1, keep=True),
    "Heading 2": S(SANS, 12, True, before=12, after=4, line=1.1, keep=True),
    "Heading 3": S(SANS, 11, True, before=10, after=3, line=1.1, keep=True),
    "Heading 4": S(SANS, 10.5, True, True, before=8, after=2, line=1.1, keep=True),
    "Bibliography": S(size=10, after=3, line=1.1, left=0.35, hanging=0.35),
    "Image Caption": S(SANS, 9.5, before=4, after=12, line=1.1),
    "Table Caption": S(SANS, 9.5, before=12, after=4, line=1.1, keep=True),
    "Table Part": S(SANS, 9.5, None, True, before=8, after=3, line=1.1, keep=True),
    "Table Note": S(SANS, 8.5, before=4, after=12, line=1.1),
    "Table Text": S(SANS, 9, before=1, after=1, line=1.0),
    "Figure Image": S(align="center", before=10, after=2, line=1.0, keep=True),
    "Display Math": S(align="center", before=4, after=6, line=1.0),
    "Footer": S(SANS, 9, after=0, line=1.0, align="center"),
}
CHAR = {"Placeholder": {}, "Verbatim Char": {}, "Hyperlink": {}}


# ---------------------------------------------------------------- XML helpers
def w(tag):
    return qn("w:" + tag)


def local(el):
    return etree.QName(el).localname


def put(parent, tag, order, **attrs):
    """Replace or insert child w:<tag> (with attributes) at its schema position; return it."""
    new = OxmlElement("w:" + tag)
    for k, v in attrs.items():
        new.set(qn("w:" + k), str(v))
    old = parent.find(w(tag))
    if old is not None:
        parent.replace(old, new)
        return new
    idx = order.index(tag)
    for c in parent:
        ln = local(c)
        if ln in order and order.index(ln) > idx:
            c.addprevious(new)
            return new
    parent.append(new)
    return new


def first_child(parent, tag):
    """Get or create w:<tag> as the first child (pPr, rPr, trPr, tcPr, tblPr all come first)."""
    c = parent.find(w(tag))
    if c is None:
        c = OxmlElement("w:" + tag)
        parent.insert(0, c)
    return c


def text_of(el):
    return "".join(t.text or "" for t in el.iter(w("t")))


def is_on(rpr, tag):
    if rpr is None:
        return False
    e = rpr.find(w(tag))
    return e is not None and e.get(w("val")) not in ("0", "false", "off")


def set_fonts(rpr, font):
    put(rpr, "rFonts", RPR_ORDER, ascii=font, hAnsi=font, cs=font, eastAsia=font)


def set_size(rpr, size):
    put(rpr, "sz", RPR_ORDER, val=int(round(size * 2)))
    put(rpr, "szCs", RPR_ORDER, val=int(round(size * 2)))


def set_flag(rpr, tag, on):
    if on:
        put(rpr, tag, RPR_ORDER)
        put(rpr, tag + "Cs", RPR_ORDER)
    else:
        put(rpr, tag, RPR_ORDER, val=0)
        put(rpr, tag + "Cs", RPR_ORDER, val=0)


def set_para(ppr, spec):
    put(ppr, "spacing", PPR_ORDER, before=int(spec["before"] * 20), after=int(spec["after"] * 20),
        line=int(round(240 * spec["line"])), lineRule="auto")
    if spec["left"] or spec["hanging"]:
        put(ppr, "ind", PPR_ORDER, left=int(spec["left"] * 1440), hanging=int(spec["hanging"] * 1440))
    put(ppr, "jc", PPR_ORDER, val=spec["align"])
    if spec["keep"]:
        put(ppr, "keepNext", PPR_ORDER)


# ---------------------------------------------------------------- styles
def strip_theme_fonts(root, sans_names=()):
    for rf in root.iter(w("rFonts")):
        for a in list(rf.attrib):
            if a.endswith("Theme"):
                del rf.attrib[a]
        if rf.get(w("ascii")) is None:
            for a in ("ascii", "hAnsi", "cs", "eastAsia"):
                rf.set(w(a), SERIF)
    for c in root.iter(w("color")):
        for a in list(c.attrib):
            if a.startswith(qn("w:theme")):
                del c.attrib[a]


def ensure_styles(doc):
    styles = doc.styles
    st_el = styles.element
    # document defaults
    dd = st_el.find(w("docDefaults"))
    if dd is not None:
        rpr = dd.find(w("rPrDefault") + "/" + w("rPr"))
        if rpr is not None:
            set_fonts(rpr, SERIF)
            set_size(rpr, 11)
    for name, spec in PARA.items():
        try:
            st = styles[name]
        except KeyError:
            st = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        if name != "Normal":
            st.base_style = styles["Normal"]
            st.quick_style = True
        ppr = st.element.get_or_add_pPr()
        set_para(ppr, spec)
        rpr = st.element.get_or_add_rPr()
        set_fonts(rpr, spec["font"])
        set_size(rpr, spec["size"])
        if spec["bold"] is not None:
            set_flag(rpr, "b", spec["bold"])
        if spec["italic"] is not None:
            set_flag(rpr, "i", spec["italic"])
        put(rpr, "color", RPR_ORDER, val="000000")
    for name in CHAR:
        try:
            st = styles[name]
        except KeyError:
            st = styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
        rpr = st.element.get_or_add_rPr()
        if name == "Placeholder":
            set_flag(rpr, "b", False)
            put(rpr, "shd", RPR_ORDER, val="clear", color="auto", fill=GREY)
        elif name == "Verbatim Char":
            set_fonts(rpr, MONO)
            set_size(rpr, 9.5)
        elif name == "Hyperlink":
            put(rpr, "color", RPR_ORDER, val="1F4E79")
    strip_theme_fonts(st_el)


def style_maps(doc):
    id2name, name2id = {}, {}
    for s in doc.styles.element.findall(w("style")):
        sid = s.get(w("styleId"))
        n = s.find(w("name"))
        name = n.get(w("val")) if n is not None else sid
        id2name[sid] = name
        name2id[name] = sid
    # python-docx/pandoc may name headings in lower case ("heading 1")
    for k in list(name2id):
        if k.lower().startswith("heading "):
            name2id["Heading " + k.split()[1]] = name2id[k]
            id2name[name2id[k]] = "Heading " + k.split()[1]
    return id2name, name2id


def page_setup(doc):
    for sec in doc.sections:
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        sec.left_margin = sec.right_margin = Inches(1)
        sec.top_margin = sec.bottom_margin = Inches(1)
        sec.header_distance = sec.footer_distance = Inches(0.5)


def add_page_numbers(doc, name2id):
    for sec in doc.sections:
        footer = sec.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        for r in list(p._p):
            if local(r) != "pPr":
                p._p.remove(r)
        ppr = first_child(p._p, "pPr")
        if "Footer" in name2id:
            put(ppr, "pStyle", PPR_ORDER, val=name2id["Footer"])
        set_para(ppr, PARA["Footer"])

        def run(child):
            r = OxmlElement("w:r")
            rpr = OxmlElement("w:rPr")
            r.append(rpr)
            set_fonts(rpr, SANS)
            set_size(rpr, 9)
            r.append(child)
            p._p.append(r)

        fc = OxmlElement("w:fldChar")
        fc.set(w("fldCharType"), "begin")
        run(fc)
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = " PAGE "
        run(it)
        fc = OxmlElement("w:fldChar")
        fc.set(w("fldCharType"), "separate")
        run(fc)
        t = OxmlElement("w:t")
        t.text = "1"
        run(t)
        fc = OxmlElement("w:fldChar")
        fc.set(w("fldCharType"), "end")
        run(fc)


# ---------------------------------------------------------------- body passes
def remove_bookmarks(body):
    n = 0
    for tag in ("bookmarkStart", "bookmarkEnd"):
        for b in list(body.iter(w(tag))):
            b.getparent().remove(b)
            n += 1
    for h in list(body.iter(w("hyperlink"))):
        if h.get(w("anchor")) is not None:          # internal link: keep the runs, drop the link
            for c in list(h):
                h.addprevious(c)
            h.getparent().remove(h)
    return n


def page_breaks(body):
    n = 0
    for p in list(body.iter(w("p"))):
        if text_of(p).strip() != PAGEBREAK:
            continue
        prev = p.getprevious()
        br_run = OxmlElement("w:r")
        br = OxmlElement("w:br")
        br.set(w("type"), "page")
        br_run.append(br)
        if prev is not None and prev.tag == w("p"):
            prev.append(br_run)                     # break at the end of the previous paragraph
            p.getparent().remove(p)
        else:
            for c in list(p):
                if local(c) != "pPr":
                    p.remove(c)
            p.append(br_run)
        n += 1
    return n


def fix_bibliography(body, id2name):
    """'1.', ' ', '<TAB>' runs from citeproc -> '1.' + w:tab, with a tab stop at the hanging indent."""
    n = 0
    stop = int(PARA["Bibliography"]["left"] * 1440)
    for p in body.iter(w("p")):
        if para_style_name(p, id2name) != "Bibliography":
            continue
        runs = [c for c in p if local(c) == "r"]
        for a, b_ in zip(runs, runs[1:]):
            if text_of(a) == " " and text_of(b_).startswith("\t"):
                p.remove(a)
        for r in p.iter(w("r")):
            t = r.find(w("t"))
            if t is None or "\t" not in (t.text or ""):
                continue
            pieces = t.text.split("\t")
            r.remove(t)
            for k, piece in enumerate(pieces):
                if k:
                    r.append(OxmlElement("w:tab"))
                if piece:
                    nt = OxmlElement("w:t")
                    nt.text = piece
                    nt.set(qn("xml:space"), "preserve")
                    r.append(nt)
        ppr = first_child(p, "pPr")
        tabs = put(ppr, "tabs", PPR_ORDER)
        tab = OxmlElement("w:tab")
        tab.set(w("val"), "left")
        tab.set(w("pos"), str(stop))
        tabs.append(tab)
        n += 1
    return n


def set_style(p, name, name2id):
    ppr = first_child(p, "pPr")
    put(ppr, "pStyle", PPR_ORDER, val=name2id[name])


def para_style_name(p, id2name):
    ps = p.find(w("pPr") + "/" + w("pStyle"))
    return id2name.get(ps.get(w("val")), "Normal") if ps is not None else "Normal"


def has_drawing(p):
    return p is not None and p.tag == w("p") and next(p.iter(w("drawing")), None) is not None


def split_runs(p, offset):
    """Split the direct run children of paragraph p at character `offset`; return (before, after)."""
    before, after, pos = [], [], 0
    for r in [c for c in p if local(c) != "pPr"]:
        txt = text_of(r)
        if pos >= offset:
            after.append(r)
        elif pos + len(txt) <= offset or local(r) != "r":
            before.append(r)
        else:
            k = offset - pos
            ts = r.findall(w("t"))
            r2 = copy.deepcopy(r)
            t1, t2 = ts[0], r2.findall(w("t"))[0]
            t1.text, t2.text = txt[:k], txt[k:]
            for t in (t1, t2):
                t.set(qn("xml:space"), "preserve")
            for extra in ts[1:]:
                r.remove(extra)
            for extra in r2.findall(w("t"))[1:]:
                r2.remove(extra)
            r.addnext(r2)
            before.append(r)
            after.append(r2)
        pos += len(txt)
    return before, after


TABLE_CAP = re.compile(r"^Table (S?\d+(?:-[A-Z]?\d+)?)\.(\s|$)")
PART_LBL = re.compile(r"^Part [A-Z]\b")
FIG_CAP = re.compile(r"^Figure (S?\d+(?:-\d+)?)\.\s")


def run_flag(r, tag):
    return is_on(r.find(w("rPr")), tag)


def table_captions(body, name2id):
    """Caption above each table group (title only, bold); the rest of the legend below as a note."""
    n_cap = n_note = 0
    for p in list(body.iter(w("p"))):
        if p.getparent() is not body or not TABLE_CAP.match(text_of(p).strip()):
            continue
        group, parts, nxt = [], [], p.getnext()
        while nxt is not None:
            if nxt.tag == w("tbl"):
                group.append(nxt)
            elif nxt.tag == w("p") and not text_of(nxt).strip() and not has_drawing(nxt):
                pass
            elif nxt.tag == w("p") and PART_LBL.match(text_of(nxt).strip()):
                parts.append(nxt)
            else:
                break
            nxt = nxt.getnext()
        if not group:
            continue
        runs = [c for c in p if local(c) != "pPr"]
        txt = text_of(p)
        lead_ws = len(txt) - len(txt.lstrip())
        if runs and run_flag(runs[0], "b"):
            k = 0
            while k < len(runs) and (run_flag(runs[k], "b") or not text_of(runs[k]).strip()) \
                    and not (runs[k].find(w("rPr") + "/" + w("rStyle")) is not None):
                k += 1
            # trailing whitespace-only runs belong to the note
            while k > 0 and not text_of(runs[k - 1]).strip():
                k -= 1
            title, note = runs[:k], runs[k:]
            all_italic = False
        else:
            m = TABLE_CAP.match(txt.strip())
            rest = txt[lead_ws + m.end():]
            s = re.search(r"\.(?=\s|$)", rest)
            cut = lead_ws + m.end() + (s.end() if s else len(rest))
            title, note = split_runs(p, cut)
            all_italic = all(run_flag(r, "i") for r in runs if text_of(r).strip())
        for r in title:
            rpr = first_child(r, "rPr")
            set_flag(rpr, "b", True)
            set_flag(rpr, "i", False)
        set_style(p, "Table Caption", name2id)
        n_cap += 1
        for q in parts:
            set_style(q, "Table Part", name2id)
        note = [r for r in note if r.getparent() is p]
        if not "".join(text_of(r) for r in note).strip():
            for r in note:
                p.remove(r)
            continue
        np_ = OxmlElement("w:p")
        set_style(np_, "Table Note", name2id)
        lbl = OxmlElement("w:r")
        lrpr = OxmlElement("w:rPr")
        lbl.append(lrpr)
        set_flag(lrpr, "i", True)
        lt = OxmlElement("w:t")
        lt.text = "Note: "
        lt.set(qn("xml:space"), "preserve")
        lbl.append(lt)
        np_.append(lbl)
        first = True
        for r in note:
            p.remove(r)
            if first and local(r) == "r":
                t = r.find(w("t"))
                if t is not None and t.text:
                    t.text = t.text.lstrip()
                    if not t.text:
                        continue
                first = False
            if all_italic and local(r) == "r":
                set_flag(first_child(r, "rPr"), "i", False)
            np_.append(r)
        group[-1].addnext(np_)
        n_note += 1
    return n_cap, n_note


NOTE_LBL = re.compile(r"^Notes?:")


def table_notes(body, name2id):
    """A 'Note: ...' paragraph right after a table becomes a table note with an italic label."""
    n = 0
    for tbl in [t for t in body if t.tag == w("tbl")]:
        nxt = tbl.getnext()
        while nxt is not None and nxt.tag == w("p") and not text_of(nxt).strip():
            nxt = nxt.getnext()
        if nxt is None or nxt.tag != w("p"):
            continue
        txt = text_of(nxt)
        m = NOTE_LBL.match(txt.lstrip())
        if not m:
            continue
        set_style(nxt, "Table Note", name2id)
        lead, _ = split_runs(nxt, len(txt) - len(txt.lstrip()) + m.end())
        for r in lead:
            if local(r) == "r":
                set_flag(first_child(r, "rPr"), "i", True)
        n += 1
    return n


def classify(body, name2id, id2name):
    counts = dict(figures=0, fig_captions=0, equations=0)
    for p in list(body.iter(w("p"))):
        if p.getparent() is not body:
            continue
        if has_drawing(p):
            set_style(p, "Figure Image", name2id)
            counts["figures"] += 1
            continue
        if next(p.iter("{%s}oMathPara" % M_NS), None) is not None:
            set_style(p, "Display Math", name2id)
            for mp in p.iter("{%s}oMathPara" % M_NS):
                mpp = mp.find("{%s}oMathParaPr" % M_NS)
                if mpp is None:
                    mpp = etree.SubElement(mp, "{%s}oMathParaPr" % M_NS)
                    mp.insert(0, mpp)
                for j in mpp.findall("{%s}jc" % M_NS):
                    mpp.remove(j)
                jc = etree.SubElement(mpp, "{%s}jc" % M_NS)
                jc.set("{%s}val" % M_NS, "center")
            counts["equations"] += 1
            continue
        txt = text_of(p).strip()
        if FIG_CAP.match(txt):
            runs = [c for c in p if local(c) == "r"]
            if has_drawing(p.getprevious()) or (runs and run_flag(runs[0], "b")):
                set_style(p, "Image Caption", name2id)
                counts["fig_captions"] += 1
    return counts


def bake(body, id2name):
    """Write each paragraph's style as direct paragraph and run formatting."""
    for p in body.iter(w("p")):
        in_table = next((a for a in p.iterancestors() if a.tag == w("tbl")), None) is not None
        name = "Table Text" if in_table else para_style_name(p, id2name)
        spec = PARA.get(name) or PARA["Normal"]
        ppr = first_child(p, "pPr")
        numbered = ppr.find(w("numPr")) is not None
        set_para(ppr, spec)
        if numbered and not in_table:                     # list items: tight, keep list indents
            put(ppr, "spacing", PPR_ORDER, before=0, after=40, line=int(round(240 * spec["line"])),
                lineRule="auto")
        for r in p.iter(w("r")):
            rpr = first_child(r, "rPr")
            rs = rpr.find(w("rStyle"))
            rname = id2name.get(rs.get(w("val")), "") if rs is not None else ""
            if rname == "Verbatim Char":
                set_fonts(rpr, MONO)
                set_size(rpr, spec["size"] - 1.5)
            else:
                set_fonts(rpr, spec["font"])
                set_size(rpr, spec["size"])
            if spec["bold"] is not None:
                set_flag(rpr, "b", spec["bold"])
            if spec["italic"] is not None and not is_on(rpr, "i"):
                set_flag(rpr, "i", spec["italic"])
            if rname == "Hyperlink":
                put(rpr, "color", RPR_ORDER, val="1F4E79")
            elif rpr.find(w("color")) is None:
                put(rpr, "color", RPR_ORDER, val="000000")
            if rname == "Placeholder":
                set_flag(rpr, "b", False)
                put(rpr, "shd", RPR_ORDER, val="clear", color="auto", fill=GREY)


# ---------------------------------------------------------------- tables
NUMERIC = re.compile(r"^(?:[+\-−–]?\s*\.?\d|[<>≤≥~]\s*\.?\d|[—–\-]$|n/?a$)", re.I)


def is_numeric_col(texts, j):
    body = [r[j].strip() for r in texts[1:] if j < len(r) and r[j].strip()]
    if not body:
        return False
    hits = sum(bool(NUMERIC.match(c)) for c in body)
    return hits / len(body) >= 0.7 and any(re.search(r"\d", c) for c in body)


WS = re.compile(r"[ \t\n]+")          # break points (not the no-break spaces inside CIs)
NUM_ = r"[+\-−–]?\s?[\d.,]+%?"
CI_GROUP = re.compile(r"[(\[]\s*" + NUM_ + r"\s*(?:to|,|–)\s*" + NUM_ + r"\s*[)\]]")  # "(−1.70 to −0.18)"


def col_widths(texts, ncols, size, cell_lr=None, protect=()):
    cw = 0.54 * size * 20                   # dxa per character (Arial digits are 0.556 em)
    pad = 2 * (CELL_LR if cell_lr is None else cell_lr) + 30
    cap = 2.9 * 1440
    mins, prefs, long_ = [], [], []
    for j in range(ncols):
        col = [r[j] if j < len(r) else "" for r in texts]
        head, body = col[0], col[1:]
        tok = max([len(t) * 1.08 for t in WS.split(head)] + [len(t) for c in body for t in WS.split(c)]
                  + [1])                     # header words are bold
        mn = min(tok * cw + pad, 1.6 * 1440)
        body_w = max((len(c) for c in body), default=0) * cw + pad
        if j in protect and body_w <= 1.7 * 1440:   # short numeric cells stay on one line
            mn = max(mn, body_w)
        raw = max(body_w, min(len(head), 12) * cw + pad)
        long_.append(max(raw - cap, 0))
        prefs.append(max(min(raw, cap), mn))
        mins.append(mn)
    smin, spref = sum(mins), sum(prefs)
    if spref <= TEXT_W:
        extra = TEXT_W - spref
        tot_long = sum(long_)
        if tot_long > 0:
            ws = [pf + extra * lg / tot_long for pf, lg in zip(prefs, long_)]
        else:
            ws = [pf * TEXT_W / spref for pf in prefs]
        ok = True
    elif smin <= TEXT_W:
        extra = TEXT_W - smin
        ws = [m + (pf - m) * extra / (spref - smin) for m, pf in zip(mins, prefs)]
        ok = True
    else:
        ws = [m * TEXT_W / smin for m in mins]
        ok = False
    ws = [int(x) for x in ws]
    ws[-1] += TEXT_W - sum(ws)
    return ws, ok


def border_set(tcpr, top=None, bottom=None):
    b = put(tcpr, "tcBorders", TCPR_ORDER)
    for side, sz in (("top", top), ("left", None), ("bottom", bottom), ("right", None)):
        e = OxmlElement("w:" + side)
        if sz:
            for k, v in (("val", "single"), ("sz", sz), ("space", 0), ("color", "000000")):
                e.set(w(k), str(v))
        else:
            e.set(w("val"), "nil")
        b.append(e)


def format_table(tbl):
    rows = tbl.findall(w("tr"))
    if not rows:
        return None
    cells = [r.findall(w("tc")) for r in rows]
    ncols = max(len(c) for c in cells)
    for t in tbl.iter(w("t")):                # keep "(-1.70 to -0.18)" together on one line
        if t.text and re.search(r"\d", t.text):
            t.text = CI_GROUP.sub(lambda m: m.group(0).replace(" ", "\u00a0"), t.text)
    texts = [[text_of(tc).strip() for tc in r] for r in cells]
    numeric = [False] + [is_numeric_col(texts, j) for j in range(1, ncols)]
    prot = {j for j, n in enumerate(numeric) if n}
    for size, cell_lr, protect in ((9.0, CELL_LR, prot), (9.0, CELL_LR, ()), (8.5, CELL_LR, ()),
                                   (8.0, CELL_LR, ()), (8.0, 40, ()), (7.5, 40, ())):
        widths, ok = col_widths(texts, ncols, size, cell_lr, protect)
        if ok:
            break

    tblpr = first_child(tbl, "tblPr")
    put(tblpr, "tblW", TBLPR_ORDER, w=sum(widths), type="dxa")
    put(tblpr, "jc", TBLPR_ORDER, val="center")
    put(tblpr, "tblInd", TBLPR_ORDER, w=0, type="dxa")
    tb = put(tblpr, "tblBorders", TBLPR_ORDER)
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + side)
        e.set(w("val"), "nil")
        tb.append(e)
    put(tblpr, "tblLayout", TBLPR_ORDER, type="fixed")
    mar = put(tblpr, "tblCellMar", TBLPR_ORDER)
    for side, v in (("top", CELL_TB), ("left", cell_lr), ("bottom", CELL_TB), ("right", cell_lr)):
        e = OxmlElement("w:" + side)
        e.set(w("w"), str(v))
        e.set(w("type"), "dxa")
        mar.append(e)
    grid = tbl.find(w("tblGrid"))
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        tblpr.addnext(grid)
    for g in list(grid):
        grid.remove(g)
    for wd in widths:
        g = OxmlElement("w:gridCol")
        g.set(w("w"), str(wd))
        grid.append(g)

    last = len(rows) - 1
    for i, (tr, rc) in enumerate(zip(rows, cells)):
        trpr = tr.find(w("trPr"))
        if trpr is None:
            trpr = OxmlElement("w:trPr")
            pex = tr.find(w("tblPrEx"))
            (pex.addnext(trpr) if pex is not None else tr.insert(0, trpr))
        for tag in ("cantSplit", "tblHeader"):
            for e in trpr.findall(w(tag)):
                trpr.remove(e)
        trpr.append(OxmlElement("w:cantSplit"))
        if i == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        top = RULE_HEAVY if i == 0 else (RULE_LIGHT if i == 1 else None)
        bottom = RULE_LIGHT if i == 0 and last > 0 else None
        if i == last:
            bottom = RULE_HEAVY
        for j, tc in enumerate(rc):
            tcpr = first_child(tc, "tcPr")
            put(tcpr, "tcW", TCPR_ORDER, w=widths[min(j, ncols - 1)], type="dxa")
            border_set(tcpr, top, bottom)
            put(tcpr, "vAlign", TCPR_ORDER, val="bottom" if i == 0 else "top")
            for p in tc.iter(w("p")):
                ppr = first_child(p, "pPr")
                put(ppr, "jc", PPR_ORDER, val="right" if numeric[min(j, ncols - 1)] else "left")
                for r in p.iter(w("r")):
                    rpr = first_child(r, "rPr")
                    set_size(rpr, size)
                    if i == 0:
                        set_flag(rpr, "b", True)
    return dict(cols=ncols, rows=len(rows), size=size, fit=ok, cell_lr=cell_lr,
                numeric=sum(numeric), widths_in=[round(x / 1440, 2) for x in widths])


# ---------------------------------------------------------------- commands
def make_reference(out, pandoc="pandoc"):
    data = subprocess.run([pandoc, "--print-default-data-file", "reference.docx"], check=True,
                          capture_output=True).stdout
    with open(out, "wb") as f:
        f.write(data)
    doc = Document(out)
    ensure_styles(doc)
    page_setup(doc)
    doc.save(out)
    print(f"wrote {out}")


def polish(src, out):
    doc = Document(src)
    ensure_styles(doc)
    id2name, name2id = style_maps(doc)
    body = doc.element.body
    strip_theme_fonts(body)
    n_bm = remove_bookmarks(body)
    n_pb = page_breaks(body)
    n_cap, n_note = table_captions(body, name2id)
    n_note += table_notes(body, name2id)
    counts = classify(body, name2id, id2name)
    bake(body, id2name)
    n_bib = fix_bibliography(body, id2name)
    tables = [format_table(t) for t in body.iter(w("tbl"))]
    page_setup(doc)
    add_page_numbers(doc, name2id)
    doc.save(out)
    full = "\n".join(text_of(p) for p in body.iter(w("p")))
    bad = [s for s in ("<!--", "-->", PAGEBREAK, "@@") if s in full]
    print(f"polished {out}: {len(tables)} tables ({n_cap} captions, {n_note} notes), "
          f"{counts['figures']} figures ({counts['fig_captions']} captions), {counts['equations']} "
          f"display equations, {n_bib} references, {n_pb} page breaks, {n_bm} bookmarks removed")
    tight = [i for i, t in enumerate(tables, 1) if t and not t["fit"]]
    if tight:
        print(f"  tables whose longest words do not fit even at 7.5 pt (columns scaled): {tight}")
    small = [(i, t["size"]) for i, t in enumerate(tables, 1) if t and t["size"] < 9]
    if small:
        print(f"  tables set below 9 pt to fit the text width (table, pt): {small}")
    if bad:
        sys.exit(f"leftover markers in the output: {bad}")


def inspect(path):
    doc = Document(path)
    id2name, _ = style_maps(doc)
    body = doc.element.body
    from collections import Counter
    styles = Counter(para_style_name(p, id2name) for p in body.iter(w("p"))
                     if not any(a.tag == w("tbl") for a in p.iterancestors()))
    print("paragraph styles:", dict(styles.most_common()))
    fonts = Counter(rf.get(w("ascii")) for rf in body.iter(w("rFonts")))
    print("run fonts:", dict(fonts))
    theme = sum(1 for rf in doc.styles.element.iter(w("rFonts")) for a in rf.attrib if a.endswith("Theme"))
    print("theme-font attributes left in styles:", theme)
    for p in body.iter(w("p")):
        n = para_style_name(p, id2name)
        if n in ("Title", "Heading 1", "Heading 2"):
            print(f"  [{n}] {text_of(p)[:90]}")
    for k, t in enumerate(body.iter(w("tbl")), 1):
        prev = t.getprevious()
        while prev is not None and prev.tag == w("p") and not text_of(prev).strip():
            prev = prev.getprevious()
        cap = text_of(prev)[:70] if prev is not None and prev.tag == w("p") else "(table)"
        grid = [int(g.get(w("w"))) for g in t.find(w("tblGrid"))]
        tc0 = t.find(w("tr")).find(w("tc"))
        b = tc0.find(w("tcPr") + "/" + w("tcBorders"))
        top = b.find(w("top")).get(w("sz")) if b is not None else None
        print(f"  table {k}: {len(grid)} cols, width {sum(grid) / 1440:.2f} in, top rule sz={top}; "
              f"before: {cap}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "reference" and len(sys.argv) >= 3:
        make_reference(sys.argv[2], *(sys.argv[3:4]))
    elif cmd == "polish" and len(sys.argv) == 4:
        polish(sys.argv[2], sys.argv[3])
    elif cmd == "inspect" and len(sys.argv) == 3:
        inspect(sys.argv[2])
    else:
        sys.exit(__doc__)
