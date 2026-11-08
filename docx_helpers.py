# -*- coding: utf-8 -*-
"""Общие помощники для сборки DOCX."""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

FOREST = "173F34"
FOREST_2 = "245746"
TERRA = "C4623F"
GOLD = "D6A23F"
CREAM = "F7F2E6"
PAPER = "FFFDF7"
SAND = "EFE6D4"
LINE = "D9D0BD"
MUTED = "66736C"
INK = "1D2B25"


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


def set_run_font(run, name="Calibri", size=10.5, bold=None, italic=None, color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = rgb(color)
    return run


def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    shd.set(qn("w:val"), "clear")
    tcPr.append(shd)


def cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{tag}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def cell_borders(cell, color=LINE, size=4, left=None):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        if left and edge == "left":
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(left))
            el.set(qn("w:color"), TERRA)
        else:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(size))
            el.set(qn("w:color"), color)
        el.set(qn("w:space"), "0")
        borders.append(el)
    tcPr.append(borders)


def set_repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def set_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    run._r.append(fld)
    set_run_font(run, "Calibri", 8.5, color=MUTED)


def add_header_text(section, left, right):
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0]
    p.text = ""
    p.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), alignment=2)
    r = p.add_run(left + "\t\t" + right)
    set_run_font(r, "Calibri", 8, color=MUTED)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "6")
    bottom.set(qn("w:color"), LINE)
    pBdr.append(bottom)
    pPr.append(pBdr)
    tabs = pPr.find(qn("w:tabs"))
    if tabs is not None:
        pPr.remove(tabs)
        pPr.append(tabs)


def add_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.text = ""
    add_page_number(p)


def setup_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)
    sec.header_distance = Cm(1.0)
    sec.footer_distance = Cm(1.0)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = rgb(INK)
    normal.paragraph_format.line_spacing = 1.22
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.space_before = Pt(0)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

    for name, size, color, before, after in (
        ("Heading 1", 22, FOREST, 0, 10),
        ("Heading 2", 15, FOREST, 14, 6),
        ("Heading 3", 11.5, TERRA, 10, 4),
    ):
        st = styles[name]
        st.font.name = "Georgia"
        st.font.size = Pt(size)
        st.font.bold = False
        st.font.color.rgb = rgb(color)
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.line_spacing = 1.05
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Georgia")

    for name in ("Caption", "Quote"):
        st = styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(9)
        st.font.italic = True
        st.font.color.rgb = rgb(MUTED)

    # update fields on open
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)
    return doc


def add_cover(doc, image_path):
    sec = doc.sections[0]
    sec.left_margin = Cm(0)
    sec.right_margin = Cm(0)
    sec.top_margin = Cm(0)
    sec.bottom_margin = Cm(0)
    sec.header_distance = Cm(0)
    sec.footer_distance = Cm(0)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run()
    run.add_picture(image_path, width=Cm(21), height=Cm(29.7))
    return sec


def new_content_section(doc):
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.0)
    sec.header_distance = Cm(1.0)
    sec.footer_distance = Cm(1.0)
    return sec


def add_h1(doc, text):
    p = doc.add_heading(text, level=1)
    p.paragraph_format.page_break_before = True
    return p


def add_h2(doc, text):
    return doc.add_heading(text, level=2)


def add_h3(doc, text):
    return doc.add_heading(text, level=3)


def add_p(doc, text="", size=10.5, italic=False, color=None, bold=False, align=None, after=5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    set_run_font(run, "Calibri", size, bold=bold, italic=italic, color=color)
    return p


def add_lead(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_run_font(r, "Calibri", 11.5, italic=True, color=FOREST_2)
    return p


def add_bullets(doc, items, size=10.5, indent=0.55):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Cm(indent)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(str(item))
        set_run_font(r, "Calibri", size)


def add_numbered(doc, items, size=10.5, indent=0.55):
    for i, item in enumerate(items, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(indent)
        p.paragraph_format.first_line_indent = Cm(-0.45)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"{i}. {item}")
        set_run_font(r, "Calibri", size)


def add_hr(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), LINE)
    pBdr.append(bottom)
    pPr.append(pBdr)
    tabs = pPr.find(qn("w:tabs"))
    if tabs is not None:
        pPr.remove(tabs)
        pPr.append(tabs)


def add_callout(doc, title, text, tone="info"):
    colors = {
        "info": ("EDF3EE", FOREST_2, "i"),
        "warn": ("FBF0E9", TERRA, "!"),
        "good": ("FBF4DF", "75551A", "★"),
    }
    bg, fg, mark = colors.get(tone, colors["info"])
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    cell = table.cell(0, 0)
    set_cant_split(table.rows[0])
    shade(cell, bg)
    cell_borders(cell, color=LINE, size=4, left=18)
    cell_margins(cell, 120, 160, 120, 140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(mark + "  " + title.upper())
    set_run_font(r, "Calibri", 8.5, bold=True, color=fg)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    set_run_font(r2, "Calibri", 10, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_table(doc, headers, rows, widths=None, font_size=8.8, header_fill=FOREST, zebra=True):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    hdr = table.rows[0]
    set_repeat_header(hdr)
    set_cant_split(hdr)
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = ""
        shade(cell, header_fill)
        cell_margins(cell, 80, 90, 80, 90)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(h))
        set_run_font(r, "Calibri", 8.2, bold=True, color="FFFFFF")
        if widths:
            cell.width = Cm(widths[i])
    for ridx, row in enumerate(rows):
        new_row = table.add_row()
        set_cant_split(new_row)
        cells = new_row.cells
        for i, val in enumerate(row):
            cell = cells[i]
            cell.text = ""
            cell_margins(cell, 70, 90, 70, 90)
            if zebra and ridx % 2 == 1:
                shade(cell, "FAF6EC")
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            set_run_font(r, "Calibri", font_size, color=INK)
            if widths:
                cell.width = Cm(widths[i])
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_prompt_box(doc, prompt, label="ЗАПРОС К ИИ"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(16.6)
    cell = table.cell(0, 0)
    cell.width = Cm(16.6)
    shade(cell, FOREST)
    cell_borders(cell, color=FOREST, size=4)
    cell_margins(cell, 120, 160, 140, 160)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(label)
    set_run_font(r, "Calibri", 7.5, bold=True, color="D6A23F")
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(prompt)
    set_run_font(r2, "Calibri", 9.3, color="F7F2E6")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_write_box(doc, label, hint="", height=3.2, label_color=FOREST):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(label.upper())
    set_run_font(r, "Calibri", 8.2, bold=True, color=label_color)
    p.paragraph_format.keep_with_next = True
    if hint:
        ph = doc.add_paragraph()
        ph.paragraph_format.space_after = Pt(3)
        ph.paragraph_format.keep_with_next = True
        rh = ph.add_run(hint)
        set_run_font(rh, "Calibri", 8.5, italic=True, color=MUTED)
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(16.6)
    cell = table.cell(0, 0)
    cell.width = Cm(16.6)
    shade(cell, "FCF8EE")
    cell_borders(cell, color="D8CBB4", size=4)
    cell_margins(cell, 120, 160, 120, 160)
    cell.paragraphs[0].text = ""
    row = table.rows[0]
    row.height = Cm(height)
    row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    set_cant_split(row)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_toc(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    fldChar = OxmlElement("w:fldChar")
    fldChar.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-1" \\h \\z \\u'
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = "Оглавление обновится при открытии документа."
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(t)
    run._r.append(fldChar3)
    return p


def add_meta_table(doc, pairs, widths=(4.0, 12.6)):
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in pairs:
        row = table.add_row()
        c1, c2 = row.cells
        c1.width = Cm(widths[0])
        c2.width = Cm(widths[1])
        for c in (c1, c2):
            cell_margins(c, 70, 100, 70, 100)
            cell_borders(c, color="E3D8C4", size=4)
        shade(c1, "F3EBDD")
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(k.upper())
        set_run_font(r1, "Calibri", 7.5, bold=True, color=MUTED)
        p2 = c2.paragraphs[0]
        p2.paragraph_format.space_after = Pt(0)
        r2 = p2.add_run(v)
        set_run_font(r2, "Calibri", 9.2, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_section_label(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text.upper())
    set_run_font(r, "Calibri", 8.2, bold=True, color=TERRA)
    return p
