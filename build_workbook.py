# -*- coding: utf-8 -*-
"""Сборка рабочей тетради участника (DOCX)."""

from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from course_data import COURSE, MODULES, PROJECT_FIELDS, RUBRIC, CHECKLISTS, GLOSSARY, PROMPTS
from docx_helpers import (
    setup_document, add_cover, new_content_section, add_header_text, add_footer,
    add_h1, add_h2, add_h3, add_p, add_lead, add_bullets, add_numbered, add_hr,
    add_callout, add_table, add_prompt_box, add_meta_table, add_section_label,
    add_write_box, FOREST, TERRA, GOLD, MUTED, LINE,
)


def add_h1_top(doc, text):
    return doc.add_heading(text, level=1)


def hours_label(h):
    h = int(h)
    if h % 10 == 1 and h % 100 != 11:
        return f"{h} академический час"
    if h % 10 in (2, 3, 4) and h % 100 not in (12, 13, 14):
        return f"{h} академических часа"
    return f"{h} академических часов"


def box_height(rows, minimum=2.8, maximum=7.0):
    return max(minimum, min(maximum, rows * 0.62))


def add_module_workbook(doc, m):
    n = m["n"]
    add_h1(doc, f"Модуль {n:02d}. {m['title']}")
    add_lead(doc, m["lede"])
    add_meta_table(doc, [
        ("Время", f"{hours_label(m['hours'])} · {m['minutes']} минут"),
        ("Результат", m["result"]),
    ])
    add_h2(doc, "Цели модуля")
    for g in m["goals"]:
        add_p(doc, "□ " + g, size=10)
    add_h2(doc, "Мой стартовый вопрос")
    add_p(doc, "Что я хочу понять или сделать на этом модуле? Сформулируйте один вопрос от своей практики.", size=9.6, color=MUTED)
    add_write_box(doc, "Старт", hint="Например: как использовать ИИ для подготовки вопросов по моей теме?", height=3.0)

    practices = [b for b in m["blocks"] if b["t"] == "practice"]
    for idx, p in enumerate(practices, 1):
        add_h2(doc, clean_title(p["title"]))
        add_p(doc, p.get("intro", ""), size=9.8)
        if p.get("prompt"):
            add_prompt_box(doc, p["prompt"])
        if p.get("steps"):
            add_p(doc, "Шаги:", size=9.2, bold=True, color=FOREST)
            add_bullets(doc, p["steps"], size=9.4)
        for f in p.get("fields", []):
            hint = " ".join(f.get("ph", "").split())
            if len(hint) > 220:
                hint = hint[:217] + "…"
            add_write_box(doc, f["label"], hint=hint, height=box_height(f.get("rows", 4), 2.8, 7.0))
        if p.get("note"):
            add_p(doc, p["note"], size=8.8, italic=True, color=MUTED)

    quiz = next((b for b in m["blocks"] if b["t"] == "quiz"), None)
    if quiz:
        add_h2(doc, "Самопроверка")
        add_p(doc, "Ответьте письменно, не подглядывая в модуль. Затем сверьтесь с онлайн-курсом или ключом в методических рекомендациях.", size=9.2, color=MUTED)
        for i, item in enumerate(quiz["items"], 1):
            add_p(doc, f"{i}. {item['q']}", size=9.9, bold=True)
        add_write_box(doc, "Мои ответы", hint="Запишите ответы и одну заметку о том, что нужно перепроверить.", height=6.0)

    art = next((b for b in m["blocks"] if b["t"] == "artifact"), None)
    if art:
        add_h2(doc, "Результат модуля")
        add_callout(doc, "Что сохранить", art["x"], "good")
        for x in art.get("items", []):
            add_p(doc, "□ " + x, size=9.6)
        add_write_box(doc, "Что у меня получилось", hint="Коротко опишите артефакт и что в нём нужно доработать.", height=4.2)

    add_h2(doc, "Заметки")
    add_write_box(doc, "Мои заметки", height=3.2)
    add_p(doc, "Межмодульная работа: 20–30 минут на доработку артефакта перед следующей встречей.", size=8.6, italic=True, color=MUTED)


def clean_title(text):
    return text


def build_workbook():
    doc = setup_document()
    doc.core_properties.title = "ИИ для образования. Рабочая тетрадь участника"
    doc.core_properties.subject = "Практикум для преподавателей колледжа"
    doc.core_properties.author = "Учебно-методический пакет «ИИ для образования»"
    doc.core_properties.keywords = "ИИ, образование, СПО, рабочая тетрадь, преподаватель"

    add_cover(doc, "assets/cover_workbook.png")
    sec = new_content_section(doc)
    add_header_text(sec, "Рабочая тетрадь · ИИ для образования", "16 академических часов")
    add_footer(sec)

    add_h1_top(doc, "Как работать с тетрадью")
    add_lead(doc, "Это ваша рабочая тетрадь. В ней вы фиксируете результаты восьми модулей и постепенно собираете итоговый учебный сценарий по своей дисциплине.")
    add_p(doc, "Тетрадь можно заполнять от руки или на компьютере. Если вы проходите онлайн-курс, те же поля доступны на сайте; тетрадь помогает не потерять материалы и подготовиться к защите проекта.")
    add_h2(doc, "Пять правил")
    add_numbered(doc, [
        "Выберите одну тему из своей дисциплины и работайте с ней на протяжении всего курса.",
        "Заполняйте раздел после каждого модуля, пока материал ещё свеж в памяти.",
        "Проверяйте ответы ИИ по учебнику, программе или надёжному источнику.",
        "Не записывайте в тетрадь персональные данные студентов и закрытые сведения.",
        "Собирайте артефакты в одну папку — они станут основой итогового проекта.",
    ], size=9.8)
    add_h2(doc, "Мои данные")
    add_write_box(doc, "Имя и фамилия", height=2.1)
    add_write_box(doc, "Организация", height=2.1)
    add_write_box(doc, "Дисциплина", height=2.1)
    add_write_box(doc, "Дата начала курса", height=2.1)

    add_callout(doc, "Безопасность", "Не загружайте в публичные ИИ-сервисы персональные данные студентов, закрытые документы и материалы ограниченного доступа. Ответ ИИ — черновик, который проверяет преподаватель.", "warn")

    add_h2(doc, "Что понадобится")
    add_bullets(doc, [
        "тема и программа вашей дисциплины;",
        "учебник или надёжный источник для проверки;",
        "компьютер или смартфон и доступ хотя бы к одному ИИ-сервису;",
        "папка для сохранения результатов;",
        "около 16 академических часов времени.",
    ], size=9.8)

    add_h2(doc, "Карта прогресса")
    rows = []
    for num, title, hours, artifact in COURSE["module_map"]:
        rows.append([num, title, f"{hours} акад. ч.", artifact, "□"])
    rows.append(["", "Итоговый проект", "2 акад. ч.", "Учебный сценарий", "□"])
    add_table(doc, ["№", "Модуль", "Время", "Артефакт", "Готово"], rows, widths=(1.0, 6.6, 2.1, 5.7, 1.2), font_size=7.8)

    add_h2(doc, "Мой план")
    add_p(doc, "Какой результат я хочу получить к концу курса? Что я принесу в свою группу?", size=9.5, color=MUTED)
    add_write_box(doc, "План", height=4.6)

    for m in MODULES:
        add_module_workbook(doc, m)

    # Final project
    add_h1(doc, "Итоговый проект")
    add_lead(doc, "Соберите фрагмент учебного сценария по своей дисциплине. В нём должно быть видно, какую задачу выполнял ИИ, что проверил преподаватель и где остаётся его ответственность.")
    add_h2(doc, "Что входит в проект")
    add_numbered(doc, [
        "тема, аудитория и наблюдаемая учебная цель;",
        "краткий план фрагмента занятия;",
        "учебный материал или объяснение;",
        "задание для студентов;",
        "критерии оценивания;",
        "один вариант дифференциации;",
        "правила использования ИИ для студентов;",
        "описание проверки и правок преподавателя;",
        "обоснование использования ИИ.",
    ], size=9.7)
    add_callout(doc, "Как заполнять", "Пишите не «красиво», а проверяемо: что студент делает, как преподаватель увидит результат и что именно было изменено после ИИ. Черновики модулей можно переносить сюда после проверки.", "info")

    for f in PROJECT_FIELDS:
        add_h2(doc, f["label"])
        add_p(doc, f["hint"], size=9.2, color=MUTED)
        add_write_box(doc, "Мой вариант", height=box_height(f["rows"], 3.0, 8.0))

    add_h2(doc, "Самооценка по рубрике")
    add_p(doc, "Отметьте один уровень для каждого критерия. Это самопроверка, а не автоматическая оценка. Итоговое решение принимает преподаватель или эксперт организации.", size=9.4, color=MUTED)
    rows = []
    for r in RUBRIC:
        rows.append([
            r["title"] + ". " + r["question"],
            "□ " + r["levels"][0],
            "□ " + r["levels"][1],
            "□ " + r["levels"][2],
            "____",
        ])
    add_table(doc, ["Критерий", "0", "1", "2", "Мой балл"], rows, widths=(3.1, 4.1, 4.1, 4.1, 1.2), font_size=7.2)

    add_p(doc, "Итого: ______ из 16.", size=11, bold=True, color=FOREST)
    add_table(doc, ["Баллы", "Ориентир"], [
        ["14–16", "Сценарий готов к апробации."],
        ["10–13", "Сценарий стоит доработать по отмеченным критериям."],
        ["0–9", "Проверьте связь цели, задания и критериев; возможно, проект ещё не собран."],
    ], widths=(3.0, 13.6), font_size=8.8)

    add_h2(doc, "Защита проекта")
    add_p(doc, "Подготовьте выступление на 2–3 минуты. Ответьте на пять вопросов:", size=9.6)
    add_numbered(doc, [
        "Какую задачу вы поручили ИИ?",
        "Какие части ответа использовали?",
        "Что проверили и изменили?",
        "Какие риски учли?",
        "Где решение остаётся ответственностью преподавателя?",
    ], size=9.6)
    add_write_box(doc, "План защиты", hint="Тезисы, а не полный текст.", height=6.0)

    add_h2(doc, "Чек-лист перед сдачей")
    for x in [
        "Цель сформулирована наблюдаемо и проверяемо.",
        "План соответствует цели и реальному времени.",
        "Материал и задание подходят группе.",
        "Факты, расчёты и ссылки проверены.",
        "Критерии понятны студенту.",
        "Дифференциация сохраняет общую цель.",
        "Правила использования ИИ конкретны.",
        "Видно, что материал отредактирован преподавателем.",
        "Нет персональных данных и закрытых сведений.",
    ]:
        add_p(doc, "□ " + x, size=9.6)

    add_h2(doc, "Рефлексия")
    for q in [
        "Что в этом сценарии ИИ помог сделать быстрее или лучше?",
        "Что я обязательно проверил(а) и изменил(а)?",
        "Какие правила я установил(а) для студентов?",
        "Что я изменю после первой апробации?",
    ]:
        add_p(doc, q, size=9.8, bold=True)
    add_write_box(doc, "Мои выводы", height=6.0)

    add_h2(doc, "Итоговый лист")
    add_meta_table(doc, [
        ("Участник", ""),
        ("Организация", ""),
        ("Дисциплина", ""),
        ("Дата", ""),
        ("Самооценка проекта", "______ из 16"),
        ("Подпись", ""),
    ])
    add_p(doc, "Официальный документ о повышении квалификации выдаёт организация после проверки проекта. Этот лист является документом самопроверки.", size=8.4, italic=True, color=MUTED)

    # Appendix
    add_h1(doc, "Приложения")
    add_h2(doc, "Приложение 1. Мои рабочие запросы")
    add_p(doc, "Запишите 3–5 запросов, которые будете использовать в своей дисциплине. Отметьте, какие части нужно менять под тему и группу.", size=9.4, color=MUTED)
    for i in range(1, 6):
        add_write_box(doc, f"Запрос {i}", height=3.8)

    add_h2(doc, "Приложение 2. Чек-лист безопасности")
    for x in CHECKLISTS["safety"]:
        add_p(doc, "□ " + x, size=9.6)

    add_h2(doc, "Приложение 3. Чек-лист качества материала")
    for x in CHECKLISTS["quality"]:
        add_p(doc, "□ " + x, size=9.6)

    add_h2(doc, "Приложение 4. Словарь")
    add_table(doc, ["Термин", "Определение"], [[t, d] for t, d in GLOSSARY], widths=(4.0, 12.6), font_size=8.0)

    add_h2(doc, "Приложение 5. Свободная страница")
    add_write_box(doc, "Мои заметки", height=8.5)

    add_hr(doc)
    add_p(doc, "Рабочая тетрадь курса «ИИ для образования». Версия 1.0 · 2026. Материалы можно адаптировать под локальные требования организации.", size=8.6, italic=True, color=MUTED)

    out = "ИИ_для_образования_Рабочая_тетрадь.docx"
    doc.save(out)
    print(out)
    return out


if __name__ == "__main__":
    build_workbook()
