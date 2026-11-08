# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import docx_helpers as H
USERS = json.loads((BASE / "admin" / "credentials_plain.json").read_text(encoding="utf-8"))

# ---------------- XLSX ----------------
wb = Workbook()
ws = wb.active
ws.title = "Доступы"
ws.sheet_view.showGridLines = False

forest = "173F34"
terra = "C4623F"
cream = "F7F2E6"
sand = "EFE6D4"
line = "D9D0BD"

ws.merge_cells("A1:E1")
ws["A1"] = "ИИ для образования — доступы участников"
ws["A1"].font = Font(name="Georgia", size=18, color=forest)
ws["A1"].alignment = Alignment(vertical="center")
ws.row_dimensions[1].height = 34

ws.merge_cells("A2:E2")
ws["A2"] = "60 логинов и паролей. Выдайте каждому участнику одну строку. Не публикуйте этот файл."
ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="66736C")
ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
ws.row_dimensions[2].height = 28

headers = ["№", "Логин", "Пароль", "ФИО / группа", "Отметка о выдаче"]
for c, h in enumerate(headers, 1):
    cell = ws.cell(row=4, column=c, value=h)
    cell.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=forest)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = Border(bottom=Side(style="thin", color=line))
ws.row_dimensions[4].height = 28

thin = Side(style="thin", color=line)
for i, u in enumerate(USERS, start=5):
    vals = [u["n"], u["login"], u["password"], "", ""]
    for c, v in enumerate(vals, 1):
        cell = ws.cell(row=i, column=c, value=v)
        cell.font = Font(name="Consolas" if c in (2, 3) else "Calibri", size=9.5, color="1D2B25")
        cell.alignment = Alignment(horizontal="center" if c in (1, 5) else "left", vertical="center")
        cell.border = Border(bottom=thin)
        if i % 2 == 0:
            cell.fill = PatternFill("solid", fgColor="FAF6EC")
    ws.row_dimensions[i].height = 18

widths = {"A": 7, "B": 14, "C": 20, "D": 30, "E": 20}
for col, width in widths.items():
    ws.column_dimensions[col].width = width
ws.freeze_panes = "A5"
ws.auto_filter.ref = f"A4:E{4 + len(USERS)}"
dv = DataValidation(type="list", formula1='"выдан,не выдан"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"E5:E{4 + len(USERS)}")
ws.print_title_rows = "4:4"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr.fitToPage = True

ws2 = wb.create_sheet("Инструкция")
ws2.sheet_view.showGridLines = False
ws2.column_dimensions["A"].width = 110
lines = [
    ("ИИ для образования — доступы участников", 16, True, forest),
    ("", 10, False, "1D2B25"),
    ("1. Каждому участнику выдаётся один логин и один пароль из таблицы.", 11, False, "1D2B25"),
    ("2. Логин можно вводить строчными буквами; пароль чувствителен к регистру.", 11, False, "1D2B25"),
    ("3. Регистрация не требуется: участник входит с выданными данными.", 11, False, "1D2B25"),
    ("4. Прогресс сохраняется в браузере под конкретным логином.", 11, False, "1D2B25"),
    ("5. Не передавайте этот файл участникам целиком: выдавайте только одну строку.", 11, False, "1D2B25"),
    ("6. При утере пароля выдайте новый доступ или замените пароль в таблице.", 11, False, "1D2B25"),
    ("7. Для публичного сайта используйте только хеши паролей (auth-data.js), не этот файл.", 11, False, "1D2B25"),
    ("", 10, False, "1D2B25"),
    ("Файл является административным и не входит в публичный пакет курса.", 9, True, terra),
]
for r, (text, size, bold, color) in enumerate(lines, 1):
    cell = ws2.cell(row=r, column=1, value=text)
    cell.font = Font(name="Calibri", size=size, bold=bold, color=color)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    if r == 1:
        ws2.row_dimensions[r].height = 30
    elif text:
        ws2.row_dimensions[r].height = 24

wb.save(BASE / "admin" / "Доступы_60_участников.xlsx")
print("xlsx saved")

# ---------------- DOCX ----------------
doc = H.setup_document()
sec = doc.sections[0]
sec.left_margin = Cm(1.6)
sec.right_margin = Cm(1.6)
sec.top_margin = Cm(1.6)
sec.bottom_margin = Cm(1.5)
H.add_header_text(sec, "ИИ для образования · доступы участников", "Только для преподавателя")
H.add_footer(sec)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
r = p.add_run("Доступы к курсу «ИИ для образования»")
H.set_run_font(r, "Georgia", 20, color=H.FOREST)
H.add_p(doc, "60 логинов и паролей. Выдайте каждому участнику одну строку. Не публикуйте этот файл и не передавайте его группе целиком.", size=9.5, italic=True, color=H.MUTED)
H.add_p(doc, "Логин можно вводить строчными буквами; пароль чувствителен к регистру. Регистрация не требуется.", size=9.5, color=H.INK)
H.add_p(doc, "Для публичного сайта используются только хеши паролей. Этот документ — административный.", size=9, italic=True, color=H.TERRA)

rows = [[str(u["n"]), u["login"], u["password"], "", ""] for u in USERS]
table = H.add_table(doc, ["№", "Логин", "Пароль", "ФИО / группа", "Отметка"], rows, widths=(1.2, 3.3, 4.8, 4.5, 2.8), font_size=8.2)
for row in table.rows[1:]:
    for c in (1, 2):
        for par in row.cells[c].paragraphs:
            for run in par.runs:
                run.font.name = "Consolas"
                run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Consolas")

doc.add_page_break()
p = doc.add_paragraph()
r = p.add_run("Как выдать доступы")
H.set_run_font(r, "Georgia", 17, color=H.FOREST)
H.add_bullets(doc, [
    "Выдайте участнику только его логин и пароль — не весь список.",
    "Попросите проверить раскладку и регистр пароля при первом входе.",
    "Не пересылайте файл в общий чат и не публикуйте его на сайте курса.",
    "Прогресс сохраняется в браузере под конкретным логином; на общем компьютере выходите из курса после работы.",
    "При утере пароля выдайте новую строку или замените пароль в таблице и обновите хеши.",
    "Для публичного сайта используйте только auth-data.js с хешами; plain-файлы храните отдельно.",
], size=9.3)
H.add_callout(doc, "Важно", "Это ограничение доступа для учебной группы, а не полноценная защита от злоумышленника. Клиентскую проверку можно обойти; для строгой защиты нужна серверная авторизация или LMS.", "warn")

doc.save(BASE / "admin" / "Доступы_60_участников.docx")
print("docx saved")
