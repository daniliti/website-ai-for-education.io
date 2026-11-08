# -*- coding: utf-8 -*-
"""Генератор автономного онлайн-курса (index.html)."""

import json
import html
from datetime import date

from course_data import (
    COURSE, MODULES, PROMPTS, GLOSSARY, CHECKLISTS,
    PROJECT_FIELDS, RUBRIC, PROJECT_INTRO,
)

ICONS = {
    "arrow": '<path d="M4 12h15M13 6l6 6-6 6"/>',
    "check": '<path d="M4 12.5l5 5L20 6.5"/>',
    "download": '<path d="M12 3v12m0 0l4-4m-4 4l-4-4M5 21h14"/>',
    "print": '<path d="M7 8V3h10v5M7 17H4a1 1 0 01-1-1V9a1 1 0 011-1h16a1 1 0 011 1v7a1 1 0 01-1 1h-3M7 14h10v7H7z"/>',
    "copy": '<rect x="8" y="8" width="11" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H5a2 2 0 00-2 2v9a2 2 0 002 2h3"/>',
    "book": '<path d="M4 5.5A2.5 2.5 0 016.5 3H20v17H6.5A2.5 2.5 0 004 22V5.5z"/><path d="M4 17.5A2.5 2.5 0 016.5 15H20"/>',
    "spark": '<path d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3z"/><path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 12l9 5 9-5M3 16l9 5 9-5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
}


def icon(name, cls="icon"):
    return (
        f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{ICONS.get(name, "")}</svg>'
    )


def esc(value):
    return html.escape(str(value), quote=True)


def render_table(head, rows):
    th = "".join(f"<th>{c}</th>" for c in head)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table class="data"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def render_checklist(cid, items):
    rows = []
    for i, item in enumerate(items):
        rows.append(
            f'<label class="check-item"><input type="checkbox" data-check="{cid}.{i}">'
            f'<span>{item}</span></label>'
        )
    return (
        f'<div class="checklist" data-checklist="{cid}">'
        + "".join(rows)
        + f'<div class="checklist-foot"><span class="checklist-count">0 из {len(items)}</span>'
        + '<button type="button" class="text-btn" data-reset-checklist>Сбросить</button></div></div>'
    )


def render_practice(block, module_n):
    fields = []
    for f in block.get("fields", []):
        fields.append(
            '<label class="field">'
            f'<span class="field-label">{f["label"]}</span>'
            f'<textarea data-store="responses.{esc(f["key"])}" rows="{f.get("rows", 4)}" '
            f'placeholder="{esc(f.get("ph", ""))}"></textarea>'
            '</label>'
        )
    steps = ""
    if block.get("steps"):
        steps = '<ol class="practice-steps">' + "".join(f"<li>{s}</li>" for s in block["steps"]) + "</ol>"
    prompt = ""
    if block.get("prompt"):
        prompt = (
            '<div class="prompt-box"><div class="prompt-top"><span>Запрос к ИИ</span>'
            f'<button type="button" class="copy-btn" data-copy>{icon("copy")} Копировать</button></div>'
            f'<p class="prompt-text">{block["prompt"]}</p></div>'
        )
    checklist = ""
    if block.get("checklist_id"):
        checklist = render_checklist(block["checklist_id"], CHECKLISTS[block["checklist_id"]])
    note = f'<p class="practice-note">{block["note"]}</p>' if block.get("note") else ""
    return (
        f'<section class="practice-card" id="practice-{module_n}-{abs(hash(block["title"])) % 10000}">'
        f'<div class="practice-head"><span class="tag tag-terra">{block.get("badge", "Практика")}</span>'
        f'<h3>{block["title"]}</h3></div>'
        f'<p class="practice-intro">{block.get("intro", "")}</p>'
        f'{prompt}{steps}<div class="fields">{"".join(fields)}</div>{checklist}{note}</section>'
    )


def render_classify(block):
    rows = []
    for i, item in enumerate(block["items"]):
        opts = "".join(
            f'<option value="{j}">{esc(opt)}</option>' for j, opt in enumerate(block["options"])
        )
        rows.append(
            f'<div class="classify-row" data-classify-row data-correct="{item["correct"]}" data-note="{esc(item["note"])}">'
            f'<span>{item["text"]}</span>'
            f'<select aria-label="Категория для задачи"><option value="">Выберите…</option>{opts}</select>'
            f'<span class="classify-feedback"></span></div>'
        )
    return (
        f'<div class="classify" data-classify><p class="small"><strong>{block["title"]}.</strong> {block["intro"]}</p>'
        + "".join(rows)
        + '<div class="quiz-actions"><button type="button" class="btn btn-primary btn-sm" data-check-classify>'
        + f'{icon("check")} Проверить распределение</button>'
        + '<span class="quiz-result" aria-live="polite"></span></div></div>'
    )


def render_quiz(module_n, items):
    rows = []
    for i, item in enumerate(items):
        opts = []
        for j, opt in enumerate(item["options"]):
            correct = ' data-correct="1"' if j == item["correct"] else ""
            opts.append(
                f'<label class="quiz-option"{correct}><input type="radio" name="quiz-{module_n}-{i}" value="{j}">'
                f'<span>{opt}</span></label>'
            )
        rows.append(
            f'<div class="quiz-item" data-qindex="{i}"><p class="quiz-q">{i+1}. {item["q"]}</p>'
            f'<div class="quiz-options">{"".join(opts)}</div>'
            f'<p class="quiz-explain"><strong>Почему:</strong> {item["explain"]}</p></div>'
        )
    return (
        f'<section class="quiz" data-module="{module_n}" data-total="{len(items)}">'
        f'<div class="quiz-head"><h3>Проверьте себя</h3><span class="tag">{len(items)} вопросов</span></div>'
        f'{"".join(rows)}'
        '<div class="quiz-actions">'
        '<button type="button" class="btn btn-primary btn-sm check-quiz">Проверить</button>'
        '<button type="button" class="btn btn-ghost btn-sm retry-quiz">Заново</button>'
        '<span class="quiz-result" aria-live="polite"></span>'
        '</div></section>'
    )


def render_blocks(blocks, module_n):
    out = []
    for b in blocks:
        t = b["t"]
        if t == "h2":
            out.append(f'<h2 class="section-title">{b["x"]}</h2>')
        elif t == "p":
            out.append(f'<p class="prose">{b["x"]}</p>')
        elif t == "lead":
            out.append(f'<p class="lead">{b["x"]}</p>')
        elif t == "list":
            out.append('<ul class="clean-list">' + "".join(f"<li>{x}</li>" for x in b["items"]) + "</ul>")
        elif t == "num":
            out.append('<ol class="num-list">' + "".join(f"<li>{x}</li>" for x in b["items"]) + "</ol>")
        elif t == "quote":
            out.append(f'<blockquote class="callout tone-good"><div class="ico">“</div><div><p>{b["x"]}</p></div></blockquote>')
        elif t == "callout":
            out.append(
                f'<aside class="callout tone-{b.get("tone","info")}"><div class="ico">'
                f'{"!" if b.get("tone") == "warn" else "i"}</div><div><h4>{b["title"]}</h4><p>{b["x"]}</p></div></aside>'
            )
        elif t == "table":
            out.append(render_table(b["head"], b["rows"]))
        elif t == "comparison":
            out.append(
                f'<div class="comparison"><div class="compare-card bad"><h4>{b["left_title"]}</h4><p>{b["left"]}</p></div>'
                f'<div class="compare-arrow">{icon("arrow")}</div>'
                f'<div class="compare-card good"><h4>{b["right_title"]}</h4><p>{b["right"]}</p></div></div>'
                f'<p class="caption">{b["caption"]}</p>'
            )
        elif t == "practice":
            out.append(render_practice(b, module_n))
        elif t == "classify":
            out.append(render_classify(b))
        elif t == "quiz":
            out.append(render_quiz(module_n, b["items"]))
        elif t == "checklist":
            out.append(render_checklist(b["id"], CHECKLISTS[b["id"]]))
        elif t == "scenarios":
            cards = []
            for s in b["items"]:
                cards.append(
                    f'<article class="scenario"><h4>{s["title"]}</h4><p>{s["text"]}</p>'
                    f'<p><strong>{s["question"]}</strong></p><details><summary>Показать ориентир</summary>'
                    f'<p>{s["answer"]}</p></details></article>'
                )
            out.append(f'<div class="scenario-grid">{"".join(cards)}</div>')
        elif t == "steps":
            steps = []
            for i, (title, text) in enumerate(b["items"]):
                steps.append(f'<div class="step"><div class="sn">{i+1:02d}</div><div><h4>{title}</h4><p>{text}</p></div></div>')
            out.append(f'<div class="steps">{"".join(steps)}</div>')
        elif t == "rubric_preview":
            rows = "".join(
                f'<div class="outcome-item"><strong style="min-width:150px">{title}.</strong><span>{q}</span></div>'
                for title, q in b["items"]
            )
            out.append(f'<div class="outcome-list" style="grid-template-columns:1fr">{rows}</div>')
        elif t == "artifact":
            items = "".join(f"<li>{x}</li>" for x in b.get("items", []))
            out.append(
                f'<section class="artifact"><div class="eyebrow">Результат модуля</div><h3>{b["title"]}</h3>'
                f'<p>{b["x"]}</p><ul>{items}</ul>'
                f'<button type="button" class="btn btn-sm" data-download-module="{module_n}">{icon("download")} Скачать результат модуля</button></section>'
            )
        elif t == "project_cta":
            out.append(
                '<section class="artifact" style="background:linear-gradient(135deg,#173f34,#2f6b56);color:var(--cream);border-color:#173f34">'
                '<div class="eyebrow" style="color:var(--gold)">Следующий шаг</div>'
                '<h3 style="color:var(--cream)">Соберите итоговый проект</h3>'
                '<p style="color:rgba(247,242,230,.8);max-width:62ch">Все поля уже заполнены? '
                'Откройте конструктор, проверьте сценарий по рубрике и скачайте портфолио.</p>'
                f'<a class="btn btn-cream" href="#project">{icon("arrow")} Перейти к проекту</a></section>'
            )
        else:
            out.append(f'<div class="empty-note">Неизвестный блок: {t}</div>')
    return "\n".join(out)


def hours_label(h):
    h = int(h)
    if h % 10 == 1 and h % 100 != 11:
        return f"{h} академический час"
    if h % 10 in (2, 3, 4) and h % 100 not in (12, 13, 14):
        return f"{h} академических часа"
    return f"{h} академических часов"


def render_module(m):
    n = m["n"]
    goals = "".join(f"<div>{g}</div>" for g in m["goals"])
    timing = "".join(f"<tr><td>{t}</td><td>{d}</td></tr>" for t, d in m["timing"])
    nxt = ""
    if n < 8:
        nxt = f'<a class="module-next" href="#module-{n+1}">Следующий модуль {icon("arrow")}</a>'
    else:
        nxt = f'<a class="module-next" href="#project">Перейти к итоговому проекту {icon("arrow")}</a>'
    prev = ""
    if n > 1:
        prev = f'<a class="module-next" href="#module-{n-1}">← Модуль {n-1:02d}</a>'
    return f'''
<section class="page" id="page-module-{n}" data-module="{n}" aria-labelledby="module-{n}-title">
  <div class="module-hero">
    <div class="module-num">{n:02d}</div>
    <div>
      <div class="eyebrow">Модуль {n:02d} · {hours_label(m["hours"])} · {m["minutes"]} минут</div>
      <h1 id="module-{n}-title">{m["title"]}</h1>
      <p class="lead">{m["lede"]}</p>
      <div class="result-line"><strong>Результат:</strong><span>{m["result"]}</span></div>
    </div>
  </div>
  <div class="card" style="margin-top:16px">
    <div class="eyebrow" style="margin-bottom:10px">В этом модуле вы</div>
    <div class="module-goals">{goals}</div>
    <details class="timing"><summary>План модуля · {m["minutes"]} минут</summary>
      <table class="timing-table"><tbody>{timing}</tbody></table>
    </details>
  </div>
  {render_blocks(m["blocks"], n)}
  <div class="module-footer">
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <button type="button" class="btn complete-btn" data-complete="{n}">{icon("check")} Завершить модуль</button>
      <button type="button" class="btn btn-ghost btn-sm" data-download-module="{n}">{icon("download")} Скачать</button>
    </div>
    <div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">{prev}{nxt}</div>
  </div>
</section>
'''


def render_overview():
    passport = "".join(
        f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in COURSE["passport"]
    )
    outcomes = "".join(f'<div class="outcome-item">{x}</div>' for x in COURSE["outcomes"])
    principles = "".join(
        f'<article class="card"><div class="card-num">{i+1:02d}</div><h3>{t}</h3><p>{d}</p></article>'
        for i, (t, d) in enumerate(COURSE["principles"])
    )
    route = "".join(
        f'<a class="route-card" href="#module-{num}" data-route-card="{num}">'
        f'<span class="rn">{num}</span><div><h4>{title}</h4><p>{artifact}</p></div>'
        f'<span class="check">✓</span></a>'
        for num, title, hours, artifact in COURSE["module_map"]
    )
    assessment = "".join(
        f"<tr><td><strong>{a}</strong></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in COURSE["assessment"]
    )
    faq = "".join(
        f'<details class="timing" style="margin-top:8px"><summary>{q}</summary><div style="padding:0 16px 14px;font-size:13px;color:var(--muted)">{a}</div></details>'
        for q, a in COURSE["faq"]
    )
    return f'''
<section class="page" id="page-overview" aria-labelledby="overview-title">
  <div class="hero">
    <div class="hero-copy">
      <div class="eyebrow">{COURSE["kicker"]}</div>
      <h1 id="overview-title"><span>ИИ</span> для<br><em>образования</em></h1>
      <p class="hero-sub">Практический курс для преподавателей колледжа: от первого запроса до готового учебного сценария, который можно принести в свою группу.</p>
      <div class="hero-actions">
        <a class="btn btn-cream" href="#module-1" id="hero-cta">{icon("arrow")} Начать с модуля 1</a>
        <a href="#teacher" style="display:inline-flex;align-items:center;gap:8px;color:#f7f2e6;border:1px solid rgba(247,242,230,.34);background:rgba(247,242,230,.04);border-radius:99px;padding:11px 18px;text-decoration:none;font-size:13.5px;font-weight:650;line-height:1.2">{icon("book")} Методисту</a>
      </div>
      <div class="hero-meta">
        <div><strong>16</strong> академических часов</div>
        <div><strong>8</strong> практических модулей</div>
        <div><strong>1</strong> готовый сценарий</div>
      </div>
    </div>
    <div class="hero-art" aria-hidden="true">
      <div class="orbit"></div>
      <div class="big-16">16</div>
      <div class="float-card a"><b>Формула</b>Черновик → проверка → педагогическое решение</div>
      <div class="float-card b"><b>Результат</b>Сценарий занятия с материалами, критериями и правилами</div>
      <div class="hero-stamp">практика<br>на своём<br>материале</div>
    </div>
  </div>

  <div class="section">
    <div class="grid grid-4">
      <div class="stat-card"><div class="num">16</div><div class="label">академических часов</div></div>
      <div class="stat-card" style="background:var(--terra)"><div class="num">8</div><div class="label">модулей и артефактов</div></div>
      <div class="stat-card" style="background:#2f6b56"><div class="num">720</div><div class="label">минут практики</div></div>
      <div class="stat-card" style="background:#d6a23f;color:var(--forest)"><div class="num" style="color:var(--forest)">1</div><div class="label" style="color:rgba(23,63,52,.65)">итоговый проект</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Паспорт курса</h2><p>Всё, что нужно знать до старта: аудитория, объём, формат и результат.</p></div>
    <dl class="passport">{passport}</dl>
  </div>

  <div class="section">
    <div class="section-head"><h2>Результаты обучения</h2><p>После курса участник сможет делать это самостоятельно — на материале своей дисциплины.</p></div>
    <div class="outcome-list">{outcomes}</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Как устроен модуль</h2><p>Один и тот же ритм в каждом модуле: понять, попробовать, проверить, сохранить.</p></div>
    <div class="how-grid">
      <div class="how-step"><div class="n">01</div><h4>Изучите</h4><p>Короткий материал без лишней теории.</p></div>
      <div class="how-step"><div class="n">02</div><h4>Попробуйте</h4><p>Практика на теме своей дисциплины.</p></div>
      <div class="how-step"><div class="n">03</div><h4>Проверьте себя</h4><p>Вопросы с обратной связью и объяснениями.</p></div>
      <div class="how-step"><div class="n">04</div><h4>Сохраните</h4><p>Артефакт для итогового проекта.</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Маршрут курса</h2><p>Можно идти по порядку или вернуться к нужному модулю. Прогресс сохраняется в браузере.</p></div>
    <div class="route-grid">{route}</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Принципы</h2><p>Пять правил, которые удерживают курс в практической и безопасной рамке.</p></div>
    <div class="grid grid-3">{principles}</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Оценивание</h2><p>Курс не про запоминание названий сервисов. Итог — рабочий продукт и профессиональное обоснование.</p></div>
    <div class="table-wrap"><table class="data"><thead><tr><th>Форма</th><th>Объём</th><th>Что оценивается</th></tr></thead><tbody>{assessment}</tbody></table></div>
    <p class="small">Порог готовности итогового проекта — 10 из 16 баллов. Итоговую оценку и решение о выдаче документа принимает организация.</p>
  </div>

  <div class="section">
    <div class="section-head"><h2>Настройте портфолио</h2><p>Эти данные появятся в итоговом листе и помогут подписать материалы.</p></div>
    <div class="card">
      <div class="grid grid-3">
        <label class="field"><span class="field-label">Имя и фамилия</span><input type="text" data-store="learner.name" placeholder="Как вас подписать"></label>
        <label class="field"><span class="field-label">Организация</span><input type="text" data-store="learner.org" placeholder="Колледж или организация"></label>
        <label class="field"><span class="field-label">Дисциплина</span><input type="text" data-store="learner.discipline" placeholder="Что вы преподаёте"></label>
      </div>
      <p class="small" style="margin:12px 0 0">Данные хранятся только в вашем браузере и не отправляются на сервер.</p>
    </div>
  </div>

  <div class="section">
    <aside class="callout tone-warn"><div class="ico">!</div><div><h4>До начала курса</h4><p>Выберите тему из своей дисциплины и держите под рукой программу, учебный материал или пример задания. Не загружайте в публичные сервисы персональные данные студентов, закрытые документы и материалы ограниченного доступа.</p></div></aside>
    <div class="grid grid-2">
      <div class="card"><h3>Что понадобится</h3><ul class="clean-list"><li>компьютер или смартфон;</li><li>доступ хотя бы к одному ИИ-сервису;</li><li>тема и материалы своей дисциплины;</li><li>папка для портфолио.</li></ul></div>
      <div class="card"><h3>Если доступа к сервису нет</h3><p>Преподаватель заранее готовит примеры запросов и ответов для разбора. Все практики можно выполнить на распечатках: сравнить, найти ошибки, переписать запрос, проверить материал.</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Частые вопросы</h2><p>Коротко о формате, доступе и документах.</p></div>
    {faq}
  </div>
</section>
'''


def render_project():
    fields = []
    for f in PROJECT_FIELDS:
        req = ' data-required="1"' if f.get("required") else ""
        fields.append(
            '<div class="project-field">'
            f'<label class="field"><span class="field-label">{f["label"]}</span>'
            f'<span class="field-hint">{f["hint"]}</span>'
            f'<textarea data-store="project.{esc(f["key"])}" data-project-field{req} rows="{f["rows"]}" placeholder="{esc(f["ph"])}"></textarea>'
            '</label></div>'
        )
    rubric_rows = []
    for r in RUBRIC:
        opts = []
        for score in (0, 1, 2):
            opts.append(
                f'<label class="rubric-opt"><input type="radio" name="rubric-{r["key"]}" '
                f'value="{score}" data-rubric="{r["key"]}"><span class="score">{score}</span>'
                f'<small>{r["levels"][score]}</small></label>'
            )
        rubric_rows.append(
            f'<div class="rubric-row" data-rubric-row="{r["key"]}"><div class="rubric-title">'
            f'<h4>{r["title"]}</h4><p>{r["question"]}</p></div>'
            f'<div class="rubric-options">{"".join(opts)}</div></div>'
        )
    return f'''
<section class="page" id="page-project" aria-labelledby="project-title">
  <div class="project-head">
    <div class="eyebrow" style="color:var(--gold)">Модуль 08 · итоговый проект · 2 академических часа</div>
    <h1 id="project-title">Учебный сценарий, который можно принести в группу</h1>
    <p>{PROJECT_INTRO}</p>
  </div>

  <div class="project-status">
    <div class="status-card"><strong>Заполнение проекта</strong><span class="project-count">0 из 0 обязательных полей</span><div class="progress-track"><i class="project-bar"></i></div><span class="small">Черновики модулей сохранены отдельно — переносите только то, что прошло проверку.</span></div>
    <div class="status-card"><strong>Самооценка</strong><span class="rubric-inline">0 из 16 баллов</span><div class="progress-track"><i class="rubric-bar"></i></div><span class="small">Порог готовности к апробации — 10 баллов.</span></div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Конструктор сценария</h2><p>Заполняйте по порядку. Все изменения сохраняются автоматически в браузере.</p></div>
    <div class="project-fields">{"".join(fields)}</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Самооценка по рубрике</h2><p>Выберите один уровень для каждого критерия. Это самопроверка, а не автоматическая оценка.</p></div>
    <div class="rubric">{"".join(rubric_rows)}
      <div class="rubric-summary"><div class="rubric-total"><b class="rubric-total-num">0</b> из 16 баллов</div>
      <div class="rubric-verdict" aria-live="polite">Отметьте все восемь критериев, чтобы увидеть ориентир.</div></div>
      <div class="quiz-actions"><button type="button" class="btn btn-ghost btn-sm" data-reset-rubric>Сбросить рубрику</button></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Проверка готовности</h2><p>Кнопка покажет, чего не хватает до завершения курса.</p></div>
    <div class="card">
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center"><button type="button" class="btn btn-primary" data-check-project>{icon("check")} Проверить готовность</button>
      <button type="button" class="btn" data-download-project>{icon("download")} Скачать проект</button>
      <button type="button" class="btn" data-print-project>{icon("print")} Печать / PDF</button></div>
      <p class="project-check-result" style="margin:14px 0 0;font-size:13px;color:var(--muted)"></p>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Лист завершения</h2><p>Документ самопроверки. Официальный сертификат выдаёт организация после проверки проекта.</p></div>
    <div class="certificate" id="certificate">
      <div class="cert-sub">Курс «ИИ для образования» · 16 академических часов</div>
      <h3>Лист завершения курса</h3>
      <p>Настоящий лист подтверждает, что участник прошёл все восемь модулей и собрал итоговый учебный сценарий для самопроверки.</p>
      <div class="cert-meta">
        <div><span>Участник</span><strong class="cert-name">—</strong></div>
        <div><span>Организация</span><strong class="cert-org">—</strong></div>
        <div><span>Дисциплина</span><strong class="cert-disc">—</strong></div>
        <div><span>Результат самооценки</span><strong class="cert-score">—</strong></div>
      </div>
      <p class="small">Дата: <span class="cert-date">—</span>. Документ не заменяет официальный сертификат организации.</p>
      <div class="quiz-actions"><button type="button" class="btn btn-primary btn-sm" data-print-certificate>{icon("print")} Печать листа</button></div>
      <div class="cert-locked"><strong>Лист откроется после завершения</strong><p class="cert-locked-text">Пройдите все 8 модулей, заполните обязательные поля проекта и отметьте рубрику не ниже 10 баллов.</p></div>
    </div>
  </div>

  <div class="section">
    <div class="callout tone-info"><div class="ico">i</div><div><h4>Что дальше</h4><p>Проведите фрагмент занятия в своей группе, соберите наблюдения и короткую обратную связь. Это даст материал для следующей итерации сценария — уже не в теории, а в практике.</p></div></aside>
  </div>
</section>
'''


def render_library():
    chips = sorted({p["cat"] for p in PROMPTS})
    chips_html = '<button type="button" class="filter-chip active" data-filter="all">Все</button>' + "".join(
        f'<button type="button" class="filter-chip" data-filter="{esc(c)}">{esc(c)}</button>' for c in chips
    )
    cards = []
    for p in PROMPTS:
        search = f'{p["cat"]} {p["title"]} {p["text"]}'.lower()
        cards.append(
            f'<article class="prompt-card" data-cat="{esc(p["cat"])}" data-search="{esc(search)}">'
            f'<span class="tag tag-gold">{esc(p["cat"])}</span><h3>{esc(p["title"])}</h3>'
            f'<div class="prompt-body">{p["text"]}</div>'
            f'<div class="note">{esc(p["note"])}</div>'
            f'<div class="card-actions"><span class="small">Замените [скобки]</span>'
            f'<button type="button" class="btn btn-sm" data-copy-prompt>{icon("copy")} Копировать</button></div>'
            '</article>'
        )
    return f'''
<section class="page" id="page-library" aria-labelledby="library-title">
  <div class="section-head"><div><div class="eyebrow">Инструменты</div><h1 id="library-title" style="font-size:clamp(2.4rem,4.6vw,4rem)">Библиотека запросов</h1></div><p>Готовые каркасы для типовых задач преподавателя. Адаптируйте под дисциплину, группу и цель.</p></div>
  <div class="library-tools">
    <div class="search-box"><input type="search" id="prompt-search" placeholder="Найти запрос: план, тест, обратная связь…" aria-label="Поиск по библиотеке запросов"></div>
    <span class="pill"><strong id="prompt-count">{len(PROMPTS)}</strong> запросов</span>
  </div>
  <div class="filter-chips">{chips_html}</div>
  <div class="library-count" id="library-count">Показано {len(PROMPTS)} из {len(PROMPTS)}</div>
  <div class="prompt-grid" id="prompt-grid">{"".join(cards)}</div>
  <div class="empty-note" id="prompt-empty" hidden>По этому запросу ничего не найдено. Попробуйте другое слово или выберите «Все».</div>
  <div class="section"><aside class="callout tone-info"><div class="ico">i</div><div><h4>Как пользоваться</h4><p>Скопируйте каркас, замените квадратные скобки и отправьте запрос. Затем попросите ИИ проверить ответ по критериям и исправьте сомнительные места. Не вставляйте персональные данные.</p></div></aside></div>
</section>
'''


def render_resources():
    glossary = "".join(f"<div><dt>{t}</dt><dd>{d}</dd></div>" for t, d in GLOSSARY)
    docs = f'''
    <div class="doc-links">
      <a class="doc-link" href="files/ИИ_для_образования_Методические_рекомендации.pdf" target="_blank" rel="noopener"><span class="ext">PDF</span><span><strong>Методические рекомендации</strong><span>Полный сценарий проведения курса</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Методические_рекомендации.docx"><span class="ext">DOCX</span><span><strong>Методические рекомендации</strong><span>Редактируемая версия</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Рабочая_тетрадь.pdf" target="_blank" rel="noopener"><span class="ext">PDF</span><span><strong>Рабочая тетрадь</strong><span>Для печати и заполнения</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Рабочая_тетрадь.docx"><span class="ext">DOCX</span><span><strong>Рабочая тетрадь</strong><span>Редактируемая версия</span></span></a>
    </div>
    '''
    return f'''
<section class="page" id="page-resources" aria-labelledby="resources-title">
  <div class="section-head"><div><div class="eyebrow">Инструменты</div><h1 id="resources-title" style="font-size:clamp(2.4rem,4.6vw,4rem)">Чек-листы и словарь</h1></div><p>Короткие инструменты, к которым можно возвращаться перед занятием.</p></div>

  <div class="section">
    <div class="section-head"><h2>Чек-лист безопасности</h2><p>Проверьте перед использованием материала в занятии.</p></div>
    {render_checklist("safety", CHECKLISTS["safety"])}
  </div>

  <div class="section">
    <div class="section-head"><h2>Чек-лист качества материала</h2><p>Методическая проверка после работы с ИИ.</p></div>
    {render_checklist("quality", CHECKLISTS["quality"])}
  </div>

  <div class="section">
    <div class="section-head"><h2>Шаблон правил для студентов</h2><p>Скопируйте и адаптируйте под конкретную работу.</p></div>
    <div class="prompt-box"><div class="prompt-top"><span>Шаблон</span><button type="button" class="copy-btn" data-copy>{icon("copy")} Копировать</button></div><p class="prompt-text">Для работы «[название]» использование ИИ: [разрешено / ограничено / не разрешено].
ИИ можно использовать для: [например, генерации идей, проверки плана, объяснения термина].
Нельзя использовать ИИ для: [например, представления целиком сгенерированного ответа как собственного].
Если ИИ использовался, студент должен: [например, указать инструмент и описать, для чего он применялся].
Студент отвечает за точность фактов, соблюдение инструкций и способность объяснить представленную работу.</p></div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Словарь курса</h2><p>Термины, которые используются в модулях и проекте.</p></div>
    <dl class="glossary">{glossary}</dl>
  </div>

  <div class="section">
    <div class="section-head"><h2>Материалы для скачивания</h2><p>Полные версии для проведения курса и печати.</p></div>
    {docs}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">
      <button type="button" class="btn" data-download-templates>{icon("download")} Скачать пустые шаблоны</button>
      <button type="button" class="btn btn-ghost" data-download-portfolio>{icon("download")} Скачать моё портфолио</button>
      <button type="button" class="btn btn-ghost" data-reset-progress>Сбросить прогресс</button>
    </div>
  </div>
</section>
'''


def render_teacher():
    formats = [
        ("8 занятий", "По одному модулю, 2–3 академических часа."),
        ("4 встречи", "Пары модулей: 1–2, 3–4, 5–6, 7–8."),
        ("2 дня", "Интенсив по 8 академических часов."),
        ("Асинхронно", "Самостоятельное прохождение по этому сайту и тетради."),
    ]
    format_cards = "".join(f'<div class="format-card"><strong>{a}</strong><span>{b}</span></div>' for a, b in formats)
    prep = [
        ("За 2 недели", "Согласуйте формат, соберите группу, проверьте доступ к сервисам и правила организации."),
        ("За 1 неделю", "Подготовьте распечатки с примерами ответов и шаблоны. Проверьте, что участники выбрали тему."),
        ("За 1 день", "Проверьте проектор, интернет, ссылки на сервисы и резервный офлайн-вариант."),
        ("В начале", "Напомните о персональных данных и о том, что ответ ИИ — черновик."),
        ("В конце", "Соберите артефакты, проведите самооценку, назначьте дату апробации."),
    ]
    prep_html = "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in prep)
    map_rows = "".join(
        f"<tr><td><strong>{num}</strong></td><td>{title}</td><td>{hours} акад. ч.</td><td>{artifact}</td></tr>"
        for num, title, hours, artifact in COURSE["module_map"]
    )
    return f'''
<section class="page" id="page-teacher" aria-labelledby="teacher-title">
  <div class="teacher-hero">
    <div class="eyebrow">Для методиста и ведущего</div>
    <h1 id="teacher-title">Как провести этот курс</h1>
    <p class="lead" style="max-width:65ch">Курс рассчитан на преподавателей колледжа, начинающих работать с генеративным ИИ. Его можно провести за 8 занятий, за 4 встречи, за 2 дня или полностью асинхронно.</p>
    <div class="format-grid" style="margin-top:18px">{format_cards}</div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Подготовка</h2><p>Что сделать до старта, чтобы практика не зависела от одного сервиса.</p></div>
    <ul class="prep-list">{prep_html}</ul>
  </div>

  <div class="section">
    <div class="section-head"><h2>Карта курса</h2><p>Сохраняйте ритм: короткое объяснение → практика → проверка → артефакт.</p></div>
    <div class="table-wrap"><table class="data"><thead><tr><th>№</th><th>Модуль</th><th>Время</th><th>Результат</th></tr></thead><tbody>{map_rows}</tbody></table></div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Если нет доступа к ИИ</h2><p>Курс не должен останавливаться из-за технических ограничений.</p></div>
    <div class="grid grid-2">
      <div class="card"><h3>Заранее подготовьте</h3><ul class="clean-list"><li>два ответа на один запрос — для сравнения;</li><li>ответ с намеренными ошибками — для поиска неточностей;</li><li>распечатку шаблона запроса и рубрики;</li><li>пример обезличенной работы студента.</li></ul></div>
      <div class="card"><h3>Что делают участники</h3><p>Сравнивают ответы, находят ошибки, переписывают запрос, проверяют факты по учебнику, заполняют шаблоны. Результат тот же — без необходимости входить в сервис.</p><p class="small">В методических рекомендациях есть готовые примеры и ключи для разбора.</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Оценивание</h2><p>Портфолио модулей и итоговый проект. Без автоматической оценки личности и без детекторов как единственного доказательства.</p></div>
    <div class="grid grid-3">
      <div class="card"><div class="card-num">01</div><h3>Портфолио</h3><p>Восемь артефактов: карта, запросы, комплект, дифференциация, критерии, правила, чек-лист, сценарий.</p></div>
      <div class="card"><div class="card-num">02</div><h3>Самооценка</h3><p>Восемь критериев по 0–2 балла. 10 баллов — порог готовности к апробации, 14–16 — готово.</p></div>
      <div class="card"><div class="card-num">03</div><h3>Защита</h3><p>2–3 минуты: какую задачу выполнял ИИ, что проверено, какие риски учтены, где ответственность преподавателя.</p></div>
    </div>
  </div>

  <div class="section">
    <div class="section-head"><h2>Материалы</h2><p>Полный методический пакет и рабочая тетрадь.</p></div>
    <div class="doc-links">
      <a class="doc-link" href="files/ИИ_для_образования_Методические_рекомендации.pdf" target="_blank" rel="noopener"><span class="ext">PDF</span><span><strong>Методические рекомендации</strong><span>Сценарии, тайминг, ответы, офлайн-вариант</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Рабочая_тетрадь.pdf" target="_blank" rel="noopener"><span class="ext">PDF</span><span><strong>Рабочая тетрадь</strong><span>Для печати и заполнения</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Методические_рекомендации.docx"><span class="ext">DOCX</span><span><strong>Рекомендации · DOCX</strong><span>Редактируемая версия</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_Рабочая_тетрадь.docx"><span class="ext">DOCX</span><span><strong>Тетрадь · DOCX</strong><span>Редактируемая версия</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_SCORM.zip"><span class="ext">ZIP</span><span><strong>SCORM 1.2</strong><span>Для Moodle и других LMS</span></span></a>
      <a class="doc-link" href="files/ИИ_для_образования_пакет.zip"><span class="ext">ZIP</span><span><strong>Весь пакет</strong><span>Сайт и материалы одним архивом</span></span></a>
    </div>
  </div>

  <div class="section">
    <div class="callout tone-warn"><div class="ico">!</div><div><h4>Этика и границы</h4><p>Не загружайте в публичные сервисы персональные данные, закрытые документы и материалы ограниченного доступа. Не используйте автоматические детекторы как единственное доказательство нарушения. Итоговые решения об оценивании остаются за преподавателем.</p></div></aside>
  </div>
</section>
'''


def build_html():
    modules_html = "\n".join(render_module(m) for m in MODULES)
    meta = [{"n": m["n"], "slug": m["slug"], "title": m["title"], "short": m["short"]} for m in MODULES]
    nav_modules = "".join(
        f'<a class="nav-link" href="#module-{m["n"]}" data-route-link="module-{m["n"]}">'
        f'<span class="n">{m["n"]:02d}</span><span>{m["short"]}</span></a>'
        for m in MODULES
    )
    data_json = json.dumps(
        {"modules": meta, "rubric": RUBRIC, "course": {"title": COURSE["title"], "hours": 16}},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    year = date.today().year
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ИИ для образования — практический онлайн-курс для преподавателей колледжа</title>
<meta name="description" content="Онлайн-курс из 8 модулей и 16 академических часов: генеративный ИИ, запросы, учебные материалы, дифференциация, оценивание, безопасность и итоговый проект.">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#173f34">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23173f34'/%3E%3Ctext x='32' y='41' text-anchor='middle' font-family='Georgia' font-size='26' fill='%23d6a23f'%3EИИ%3C/text%3E%3Ccircle cx='49' cy='15' r='4' fill='%23c4623f'/%3E%3C/svg%3E">
<style>
{open("site.css", encoding="utf-8").read()}
</style>
</head>
<body class="auth-locked">
<a class="skip-link" href="#main">Перейти к содержанию</a>

<div class="login-screen" id="login-screen">
  <div class="login-visual">
    <div class="login-brand">
      <span class="brand-mark">ИИ</span>
      <span class="brand-text"><strong>ИИ для образования</strong><span>практикум · 16 академических часов</span></span>
    </div>
    <div class="login-copy">
      <div class="eyebrow">Онлайн-практикум для преподавателей колледжа</div>
      <h1><span>ИИ</span> для<br><em>образования</em></h1>
      <p>Практический курс: от первого запроса до готового учебного сценария, который можно принести в свою группу.</p>
      <div class="login-points">
        <span><b>16</b> акад. часов</span>
        <span><b>8</b> модулей</span>
        <span><b>1</b> итоговый проект</span>
      </div>
    </div>
    <div class="login-visual-foot">Практика на своём материале · проверка · педагогическое решение</div>
    <div class="login-big" aria-hidden="true">16</div>
  </div>
  <div class="login-panel">
    <div class="login-card">
      <div class="eyebrow">Вход в курс</div>
      <h2>Логин и пароль</h2>
      <p class="login-sub">Регистрация не требуется. Доступ выдаёт преподаватель.</p>
      <form class="login-form" id="login-form" novalidate>
        <label class="login-field"><span>Логин</span><input id="login-user" name="username" type="text" autocomplete="username" autocapitalize="none" spellcheck="false" placeholder="например, ped01"></label>
        <label class="login-field"><span>Пароль</span><span class="pass-wrap"><input id="login-pass" name="password" type="password" autocomplete="current-password" placeholder="Введите пароль"><button type="button" class="pass-toggle" id="toggle-pass" aria-label="Показать пароль">Показать</button></span></label>
        <div class="login-row"><label class="login-check"><input type="checkbox" id="login-remember" checked> Запомнить на этом устройстве</label><button type="button" class="text-btn" id="forgot-link">Забыли пароль?</button></div>
        <button type="submit" class="btn btn-primary login-submit">Войти {icon("arrow")}</button>
        <p class="login-error" id="login-error" role="alert" aria-live="polite"></p>
      </form>
      <p class="login-note">Нет доступа? Обратитесь к преподавателю. Самостоятельная регистрация не предусмотрена.</p>
    </div>
    <p class="login-legal">Доступ ограничен для учебной группы. Не передавайте свой пароль другим участникам.</p>
  </div>
</div>

<div class="app">
  <aside class="sidebar" id="sidebar" aria-label="Навигация по курсу">
    <a class="brand" href="#overview" data-close-sidebar>
      <span class="brand-mark">ИИ</span>
      <span class="brand-text"><strong>ИИ для образования</strong><span>практикум · 16 часов</span></span>
    </a>
    <div class="progress-card">
      <svg class="ring" viewBox="0 0 54 54" aria-hidden="true"><circle class="bg" cx="27" cy="27" r="23"/><circle class="fg" cx="27" cy="27" r="23" stroke-dasharray="144.5" stroke-dashoffset="144.5"/></svg>
      <div class="progress-copy"><strong><span data-progress-done>0</span> из 8 модулей</strong><span data-progress-pct>0% курса</span></div>
    </div>
    <div class="nav-group">Курс</div>
    <a class="nav-link" href="#overview" data-route-link="overview"><span class="n">00</span><span>Обзор и паспорт</span></a>
    {nav_modules}
    <div class="nav-group">Практика</div>
    <a class="nav-link" href="#project" data-route-link="project"><span class="n">★</span><span>Итоговый проект</span></a>
    <div class="nav-group">Инструменты</div>
    <a class="nav-link" href="#library" data-route-link="library"><span class="n">↗</span><span>Библиотека запросов</span></a>
    <a class="nav-link" href="#resources" data-route-link="resources"><span class="n">✓</span><span>Чек-листы и словарь</span></a>
    <a class="nav-link" href="#teacher" data-route-link="teacher"><span class="n">i</span><span>Методисту</span></a>
    <div class="sidebar-user" id="sidebar-user-box" hidden><span>Вы вошли как <b data-current-user>—</b></span><button type="button" class="text-btn" id="logout-btn-side">Выйти</button></div>
    <div class="sidebar-foot">Версия {COURSE["version"]} · {COURSE["year"]}<br>Прогресс хранится в вашем браузере.<br><a href="#resources">Скачать материалы</a></div>
  </aside>
  <div class="sidebar-backdrop" data-close-sidebar></div>

  <div class="shell">
    <header class="topbar">
      <button class="menu-btn" type="button" id="menu-btn" aria-label="Открыть меню" aria-controls="sidebar" aria-expanded="false">☰</button>
      <div class="crumb" id="crumb"><strong>ИИ для образования</strong> · обзор курса</div>
      <div class="top-actions">
        <span class="small" id="save-status" style="color:var(--muted)">Сохранено локально</span>
        <div class="top-progress"><div class="bar"><i data-top-bar></i></div><span data-progress-pct>0%</span></div>
        <span class="user-chip" id="user-chip" hidden><span class="user-dot"></span><span data-current-user>—</span></span>
        <button type="button" class="btn btn-sm" data-download-portfolio>{icon("download")} <span>Портфолио</span></button>
        <button type="button" class="btn btn-sm btn-ghost" id="logout-btn">Выйти</button>
      </div>
    </header>

    <main class="main" id="main">
      {render_overview()}
      {modules_html}
      {render_project()}
      {render_library()}
      {render_resources()}
      {render_teacher()}
    </main>

    <footer class="site-footer">
      <span>«ИИ для образования» · практический курс для преподавателей колледжа · {year}</span>
      <span>16 академических часов <span class="dotsep"></span> 8 модулей <span class="dotsep"></span> 1 итоговый сценарий</span>
      <span><a href="#teacher">Методисту</a> · <a href="#resources">Материалы</a></span>
    </footer>
  </div>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<div class="print-sheet" id="print-sheet" aria-hidden="true"></div>

<script src="auth-data.js"></script>
<script src="auth.js"></script>
<script src="scorm.js"></script>
<script>
const DATA = {data_json};

/* ---------- storage ---------- */
const KEY_PREFIX = "aiEduCourse.v1.";
let KEY = KEY_PREFIX + "guest";
const AUTH = window.COURSE_AUTH;
const defaults = () => ({{ learner:{{}}, responses:{{}}, quiz:{{}}, completed:{{}}, project:{{}}, rubric:{{}}, checks:{{}}, lastRoute:"overview" }});
let storageOK = true;
function loadState() {{
  try {{
    const raw = localStorage.getItem(KEY);
    if (!raw) return defaults();
    const parsed = JSON.parse(raw);
    return Object.assign(defaults(), parsed, {{
      learner: Object.assign({{}}, parsed.learner || {{}}),
      responses: Object.assign({{}}, parsed.responses || {{}}),
      project: Object.assign({{}}, parsed.project || {{}}),
      rubric: Object.assign({{}}, parsed.rubric || {{}}),
      checks: Object.assign({{}}, parsed.checks || {{}}),
      quiz: Object.assign({{}}, parsed.quiz || {{}}),
      completed: Object.assign({{}}, parsed.completed || {{}})
    }});
  }} catch (e) {{
    storageOK = false;
    return defaults();
  }}
}}
let state = defaults();
let currentUser = null;
let saveTimer = null;
function saveNow() {{
  if (!storageOK) return;
  try {{ localStorage.setItem(KEY, JSON.stringify(state)); }}
  catch (e) {{ storageOK = false; showToast("Не удалось сохранить. Проверьте настройки браузера."); }}
  const el = document.getElementById("save-status");
  if (el) {{ el.textContent = "Сохранено локально"; }}
}}
function saveSoon() {{
  clearTimeout(saveTimer);
  const el = document.getElementById("save-status");
  if (el) el.textContent = "Сохраняем…";
  saveTimer = setTimeout(saveNow, 250);
}}
function getPath(obj, path) {{
  return path.split(".").reduce((acc, key) => (acc == null ? undefined : acc[key]), obj);
}}
function setPath(obj, path, value) {{
  const parts = path.split(".");
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {{
    if (typeof cur[parts[i]] !== "object" || cur[parts[i]] === null) cur[parts[i]] = {{}};
    cur = cur[parts[i]];
  }}
  cur[parts[parts.length - 1]] = value;
}}
function showToast(msg) {{
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2600);
}}

/* ---------- routing ---------- */
function routeFromHash() {{
  const h = (location.hash || "#overview").replace("#", "");
  return document.getElementById("page-" + h) ? h : "overview";
}}
function showRoute() {{
  const route = routeFromHash();
  document.querySelectorAll(".page").forEach(p => p.classList.toggle("active", p.id === "page-" + route));
  document.querySelectorAll("[data-route-link]").forEach(a => a.classList.toggle("active", a.dataset.routeLink === route));
  const meta = DATA.modules.find(m => "module-" + m.n === route);
  const crumb = document.getElementById("crumb");
  if (crumb) {{
    if (meta) crumb.innerHTML = "<strong>Модуль " + String(meta.n).padStart(2, "0") + "</strong> · " + meta.short;
    else if (route === "project") crumb.innerHTML = "<strong>Итоговый проект</strong> · учебный сценарий";
    else if (route === "library") crumb.innerHTML = "<strong>Инструменты</strong> · библиотека запросов";
    else if (route === "resources") crumb.innerHTML = "<strong>Инструменты</strong> · чек-листы и словарь";
    else if (route === "teacher") crumb.innerHTML = "<strong>Для методиста</strong> · проведение курса";
    else crumb.innerHTML = "<strong>ИИ для образования</strong> · обзор курса";
  }}
  const titles = {{ overview: "Практический онлайн-курс для преподавателей колледжа", project: "Итоговый проект", library: "Библиотека запросов", resources: "Чек-листы и словарь", teacher: "Методисту" }};
  document.title = meta ? (meta.title + " — ИИ для образования") : ((titles[route] || "ИИ для образования") + " — ИИ для образования");
  state.lastRoute = route; saveSoon();
  if (window.SCORM) {{ window.SCORM.setLocation(route); }}
  window.scrollTo(0, 0);
  document.body.classList.remove("sidebar-open");
  const mb = document.getElementById("menu-btn");
  if (mb) mb.setAttribute("aria-expanded", "false");
}}
window.addEventListener("hashchange", showRoute);

/* ---------- restore / inputs ---------- */
function restoreFields() {{
  document.querySelectorAll("[data-store]").forEach(el => {{
    const v = getPath(state, el.dataset.store);
    if (v !== undefined && v !== null) el.value = v;
  }});
}}
document.addEventListener("input", e => {{
  const el = e.target.closest("[data-store]");
  if (!el) return;
  setPath(state, el.dataset.store, el.value);
  saveSoon();
  if (el.dataset.store.startsWith("project.")) updateProjectStatus();
}});

/* ---------- progress ---------- */
function completedCount() {{
  return DATA.modules.filter(m => !!state.completed[String(m.n)]).length;
}}
function updateProgress() {{
  const done = completedCount();
  const pct = Math.round(done / DATA.modules.length * 100);
  document.querySelectorAll("[data-progress-done]").forEach(el => el.textContent = done);
  document.querySelectorAll("[data-progress-pct]").forEach(el => el.textContent = pct + "%");
  document.querySelectorAll("[data-top-bar]").forEach(el => el.style.width = pct + "%");
  const ring = document.querySelector(".ring .fg");
  if (ring) ring.style.strokeDashoffset = String(144.5 * (1 - done / DATA.modules.length));
  document.querySelectorAll("[data-route-card]").forEach(card => {{
    card.classList.toggle("is-done", !!state.completed[card.dataset.routeCard]);
  }});
  document.querySelectorAll("[data-route-link^='module-']").forEach(a => {{
    const n = a.dataset.routeLink.replace("module-", "");
    a.classList.toggle("is-done", !!state.completed[n]);
  }});
  document.querySelectorAll("[data-complete]").forEach(btn => {{
    const isDone = !!state.completed[btn.dataset.complete];
    btn.classList.toggle("is-done", isDone);
    btn.innerHTML = isDone ? "✓ Модуль завершён" : "Завершить модуль";
  }});
  const cta = document.getElementById("hero-cta");
  if (cta) {{
    const nextModule = DATA.modules.find(m => !state.completed[String(m.n)]);
    if (done >= DATA.modules.length) {{
      cta.href = "#project";
      cta.textContent = "Перейти к проекту";
    }} else if (nextModule) {{
      cta.href = "#module-" + nextModule.n;
      cta.textContent = done === 0 ? "Начать с модуля 1" : ("Продолжить: модуль " + String(nextModule.n).padStart(2, "0"));
    }}
  }}
  updateProjectStatus();
  if (window.SCORM) {{ window.SCORM.setScore(rubricTotal(), 16); window.SCORM.setCompleted(done === DATA.modules.length); }}
}}
document.addEventListener("click", e => {{
  const btn = e.target.closest("[data-complete]");
  if (!btn) return;
  const n = btn.dataset.complete;
  state.completed[n] = !state.completed[n];
  saveNow();
  updateProgress();
  showToast(state.completed[n] ? "Модуль " + n + " завершён" : "Отметка снята");
}});

/* ---------- quizzes ---------- */
function markQuiz(q, answers, notify) {{
  const n = q.dataset.module;
  const items = q.querySelectorAll(".quiz-item");
  let score = 0;
  items.forEach((item, i) => {{
    const chosen = answers[i];
    const labels = item.querySelectorAll(".quiz-option");
    labels.forEach(label => {{
      label.classList.remove("is-correct", "is-wrong");
      const input = label.querySelector("input");
      const isCorrect = label.dataset.correct === "1";
      if (isCorrect) label.classList.add("is-correct");
      if (input.checked && !isCorrect) label.classList.add("is-wrong");
      input.disabled = true;
    }});
    if (chosen !== undefined && chosen !== null) {{
      const selected = item.querySelectorAll(".quiz-option")[chosen];
      if (selected && selected.dataset.correct === "1") score++;
    }}
    item.classList.add("answered");
  }});
  q.querySelectorAll("input[type=radio]").forEach(i => i.disabled = true);
  const result = q.querySelector(".quiz-result");
  if (result) {{
    result.textContent = "Результат: " + score + " из " + items.length;
    result.classList.toggle("bad", score < Math.ceil(items.length * 0.6));
  }}
  state.quiz[n] = {{ score: score, total: items.length, answers: answers, checked: true }};
  saveNow();
  if (notify) showToast(score === items.length ? "Отлично: все ответы верные" : "Самопроверка сохранена");
}}
function evaluateQuiz(q) {{
  const n = q.dataset.module;
  const items = q.querySelectorAll(".quiz-item");
  const answers = [];
  let missing = false;
  items.forEach((item, i) => {{
    const checked = item.querySelector("input[type=radio]:checked");
    if (!checked) {{ missing = true; answers.push(null); }}
    else answers.push(Number(checked.value));
  }});
  if (missing) {{ showToast("Ответьте на все вопросы — тогда появится результат."); return; }}
  markQuiz(q, answers, true);
}}
function restoreQuizzes() {{
  document.querySelectorAll(".quiz").forEach(q => {{
    const n = q.dataset.module;
    const saved = state.quiz[n];
    if (!saved || !saved.answers) return;
    const items = q.querySelectorAll(".quiz-item");
    saved.answers.forEach((answer, i) => {{
      if (answer === null || answer === undefined) return;
      const input = q.querySelector('input[name="quiz-' + n + '-' + i + '"][value="' + answer + '"]');
      if (input) input.checked = true;
    }});
    if (saved.checked) markQuiz(q, saved.answers, false);
  }});
}}
document.addEventListener("click", e => {{
  const btn = e.target.closest(".check-quiz");
  if (btn) {{ evaluateQuiz(btn.closest(".quiz")); return; }}
  const retry = e.target.closest(".retry-quiz");
  if (!retry) return;
  const q = retry.closest(".quiz");
  const n = q.dataset.module;
  delete state.quiz[n];
  saveNow();
  q.querySelectorAll(".quiz-item").forEach(item => {{
    item.classList.remove("answered");
    item.querySelectorAll(".quiz-option").forEach(label => label.classList.remove("is-correct", "is-wrong"));
    item.querySelectorAll("input[type=radio]").forEach(input => {{ input.checked = false; input.disabled = false; }});
  }});
  const result = q.querySelector(".quiz-result");
  if (result) {{ result.textContent = ""; result.classList.remove("bad"); }}
  showToast("Можно пройти самопроверку заново");
}});

/* ---------- classify ---------- */
document.addEventListener("click", e => {{
  const btn = e.target.closest("[data-check-classify]");
  if (!btn) return;
  const root = btn.closest("[data-classify]");
  const rows = root.querySelectorAll("[data-classify-row]");
  let done = 0, correct = 0;
  rows.forEach(row => {{
    const select = row.querySelector("select");
    row.classList.remove("correct", "wrong");
    row.classList.remove("show");
    if (!select.value) return;
    done++;
    const ok = Number(select.value) === Number(row.dataset.correct);
    if (ok) correct++;
    row.classList.add("show", ok ? "correct" : "wrong");
    const feedback = row.querySelector(".classify-feedback");
    if (ok) feedback.textContent = "Верно. " + row.dataset.note;
    else {{
      const correctText = select.options[Number(row.dataset.correct)].text;
      feedback.textContent = "Ориентир: «" + correctText + "». " + row.dataset.note;
    }}
  }});
  const res = root.querySelector(".quiz-result");
  if (res) {{
    if (done < rows.length) res.textContent = "Заполнено " + done + " из " + rows.length + " — проверьте все.";
    else res.textContent = "Верно " + correct + " из " + rows.length + ". Это ориентир, а не оценка.";
  }}
}});

/* ---------- checklists ---------- */
function updateChecklist(root) {{
  if (!root) return;
  const boxes = root.querySelectorAll("[data-check]");
  const checked = [...boxes].filter(b => b.checked).length;
  const count = root.querySelector(".checklist-count");
  if (count) count.textContent = checked + " из " + boxes.length;
}}
function initChecklists() {{
  document.querySelectorAll("[data-check]").forEach(box => {{
    box.checked = !!state.checks[box.dataset.check];
    const root = box.closest(".checklist");
    updateChecklist(root);
  }});
}}
document.addEventListener("change", e => {{
  const box = e.target.closest("[data-check]");
  if (!box) return;
  state.checks[box.dataset.check] = box.checked;
  saveSoon();
  updateChecklist(box.closest(".checklist"));
}});
document.addEventListener("click", e => {{
  const btn = e.target.closest("[data-reset-checklist]");
  if (!btn) return;
  const root = btn.closest(".checklist");
  root.querySelectorAll("[data-check]").forEach(box => {{
    box.checked = false;
    delete state.checks[box.dataset.check];
  }});
  saveSoon();
  updateChecklist(root);
}});

/* ---------- rubric ---------- */
function rubricTotal() {{
  return DATA.rubric.reduce((sum, r) => sum + (Number(state.rubric[r.key]) || 0), 0);
}}
function rubricSelected() {{
  return DATA.rubric.filter(r => state.rubric[r.key] !== undefined && state.rubric[r.key] !== null).length;
}}
function restoreRubric() {{
  document.querySelectorAll("[data-rubric]").forEach(input => {{
    const v = state.rubric[input.dataset.rubric];
    if (v !== undefined && Number(input.value) === Number(v)) input.checked = true;
  }});
}}
function updateRubric() {{
  const total = rubricTotal();
  const selected = rubricSelected();
  document.querySelectorAll(".rubric-total-num").forEach(el => el.textContent = total);
  document.querySelectorAll(".rubric-inline").forEach(el => el.textContent = total + " из 16 баллов");
  const bar = document.querySelector(".rubric-bar");
  if (bar) bar.style.width = Math.round(total / 16 * 100) + "%";
  document.querySelectorAll(".rubric-verdict").forEach(el => {{
    if (selected < 8) el.innerHTML = "Отметьте все восемь критериев, чтобы увидеть ориентир. Сейчас выбрано <strong>" + selected + " из 8</strong>.";
    else if (total >= 14) el.innerHTML = "<strong>14–16 баллов.</strong> Сценарий готов к апробации: осталось провести его в группе и собрать наблюдения.";
    else if (total >= 10) el.innerHTML = "<strong>10–13 баллов.</strong> Сценарий можно доработать по отмеченным критериям и затем пробовать в группе.";
    else el.innerHTML = "<strong>0–9 баллов.</strong> Проверьте связь цели, задания и критериев; возможно, проект ещё не собран полностью.";
  }});
  updateProjectStatus();
}}
document.addEventListener("change", e => {{
  const input = e.target.closest("[data-rubric]");
  if (!input) return;
  state.rubric[input.dataset.rubric] = Number(input.value);
  saveSoon();
  updateRubric();
}});
document.addEventListener("click", e => {{
  const btn = e.target.closest("[data-reset-rubric]");
  if (!btn) return;
  state.rubric = {{}};
  document.querySelectorAll("[data-rubric]").forEach(i => i.checked = false);
  saveNow();
  updateRubric();
  showToast("Рубрика сброшена");
}});

/* ---------- project / certificate ---------- */
function canCertify() {{
  const fields = [...document.querySelectorAll("#page-project [data-required='1']")];
  const filled = fields.filter(f => f.value.trim().length > 0).length;
  return completedCount() === DATA.modules.length && filled === fields.length && rubricSelected() === 8 && rubricTotal() >= 10;
}}
function updateProjectStatus() {{
  const fields = [...document.querySelectorAll("#page-project [data-required='1']")];
  const filled = fields.filter(f => f.value.trim().length > 0).length;
  document.querySelectorAll(".project-count").forEach(el => el.textContent = "Заполнено " + filled + " из " + fields.length + " обязательных полей");
  const bar = document.querySelector(".project-bar");
  if (bar) bar.style.width = (fields.length ? Math.round(filled / fields.length * 100) : 0) + "%";
  const total = rubricTotal();
  document.querySelectorAll(".rubric-inline").forEach(el => el.textContent = total + " из 16 баллов");
  const name = state.learner.name || "—";
  const org = state.learner.org || "—";
  const disc = state.learner.discipline || "—";
  document.querySelectorAll(".cert-name").forEach(el => el.textContent = name);
  document.querySelectorAll(".cert-org").forEach(el => el.textContent = org);
  document.querySelectorAll(".cert-disc").forEach(el => el.textContent = disc);
  document.querySelectorAll(".cert-score").forEach(el => el.textContent = total + " из 16");
  document.querySelectorAll(".cert-date").forEach(el => el.textContent = new Date().toLocaleDateString("ru-RU", {{ day: "numeric", month: "long", year: "numeric" }}));
  const cert = document.getElementById("certificate");
  if (cert) cert.classList.toggle("is-ready", canCertify());
  const locked = document.querySelector(".cert-locked-text");
  if (locked) {{
    const missing = [];
    if (completedCount() < DATA.modules.length) missing.push("завершите все 8 модулей");
    if (filled < fields.length) missing.push("заполните обязательные поля");
    if (rubricSelected() < 8) missing.push("отметьте все критерии");
    if (total < 10) missing.push("наберите не менее 10 баллов");
    locked.textContent = "Осталось: " + missing.join("; ") + ".";
  }}
}}
document.addEventListener("click", e => {{
  const btn = e.target.closest("[data-check-project]");
  if (!btn) return;
  const fields = [...document.querySelectorAll("#page-project [data-required='1']")];
  const empty = fields.filter(f => !f.value.trim());
  const out = document.querySelector(".project-check-result");
  if (empty.length) {{
    out.innerHTML = "<strong>Не хватает " + empty.length + " обязательных полей.</strong> Проверьте блоки: " + empty.map(f => f.closest(".project-field").querySelector(".field-label").textContent.replace(/^\\d+\\.\\s*/, "")).join("; ") + ".";
    out.style.color = "var(--terra-dark)";
  }} else if (rubricSelected() < 8) {{
    out.innerHTML = "<strong>Поля заполнены.</strong> Отметьте все восемь критериев рубрики.";
    out.style.color = "var(--terra-dark)";
  }} else if (rubricTotal() < 10) {{
    out.innerHTML = "<strong>" + rubricTotal() + " из 16.</strong> Для готовности к апробации нужно не менее 10 баллов. Вернитесь к критериям, которые получили 0.";
    out.style.color = "var(--terra-dark)";
  }} else if (completedCount() < DATA.modules.length) {{
    out.innerHTML = "<strong>Проект собран.</strong> Осталось завершить модули: " + (DATA.modules.length - completedCount()) + ".";
    out.style.color = "var(--forest)";
  }} else {{
    out.innerHTML = "<strong>Готово к самопроверке.</strong> Все модули завершены, проект заполнен, рубрика — " + rubricTotal() + " из 16. Лист завершения открыт.";
    out.style.color = "var(--forest)";
  }}
}});

/* ---------- library ---------- */
let activeFilter = "all";
function filterPrompts() {{
  const query = (document.getElementById("prompt-search")?.value || "").trim().toLowerCase();
  const cards = [...document.querySelectorAll(".prompt-card")];
  let shown = 0;
  cards.forEach(card => {{
    const okCat = activeFilter === "all" || card.dataset.cat === activeFilter;
    const okQuery = !query || card.dataset.search.includes(query);
    const show = okCat && okQuery;
    card.hidden = !show;
    if (show) shown++;
  }});
  const count = document.getElementById("library-count");
  if (count) count.textContent = "Показано " + shown + " из " + cards.length;
  const empty = document.getElementById("prompt-empty");
  if (empty) empty.hidden = shown !== 0;
}}
document.addEventListener("input", e => {{
  if (e.target.id === "prompt-search") filterPrompts();
}});
document.addEventListener("click", e => {{
  const chip = e.target.closest("[data-filter]");
  if (!chip) return;
  document.querySelectorAll("[data-filter]").forEach(c => c.classList.remove("active"));
  chip.classList.add("active");
  activeFilter = chip.dataset.filter;
  filterPrompts();
}});

/* ---------- copy ---------- */
async function copyText(text) {{
  try {{
    if (navigator.clipboard && window.isSecureContext) {{
      await navigator.clipboard.writeText(text);
      return true;
    }}
  }} catch (err) {{}}
  try {{
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  }} catch (err) {{ return false; }}
}}
document.addEventListener("click", async e => {{
  const btn = e.target.closest("[data-copy], [data-copy-prompt]");
  if (!btn) return;
  let text = "";
  if (btn.hasAttribute("data-copy-prompt")) {{
    text = btn.closest(".prompt-card")?.querySelector(".prompt-body")?.innerText || "";
  }} else {{
    text = btn.closest(".prompt-box")?.querySelector(".prompt-text")?.innerText || "";
  }}
  const ok = await copyText(text);
  showToast(ok ? "Скопировано" : "Не удалось скопировать — выделите текст вручную");
}});

/* ---------- downloads ---------- */
function downloadFile(filename, content, type) {{
  const blob = new Blob([content], {{ type: type || "text/markdown;charset=utf-8" }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}}
function fieldLabel(el) {{
  return el.closest(".field")?.querySelector(".field-label")?.textContent.trim() || "Ответ";
}}
function quizLine(n) {{
  const q = state.quiz[String(n)];
  return q ? "Самопроверка: " + q.score + " из " + q.total : "Самопроверка: не пройдена";
}}
function buildPortfolio() {{
  const now = new Date();
  const lines = [];
  lines.push("# Портфолио курса «ИИ для образования»");
  lines.push("");
  lines.push("**Участник:** " + (state.learner.name || "—"));
  lines.push("**Логин:** " + (currentUser || "—"));
  lines.push("**Организация:** " + (state.learner.org || "—"));
  lines.push("**Дисциплина:** " + (state.learner.discipline || "—"));
  lines.push("**Дата:** " + now.toLocaleDateString("ru-RU"));
  lines.push("**Прогресс:** " + completedCount() + " из 8 модулей; самооценка проекта — " + rubricTotal() + " из 16.");
  lines.push("");
  lines.push("---");
  DATA.modules.forEach(m => {{
    lines.push("");
    lines.push("## Модуль " + String(m.n).padStart(2, "0") + ". " + m.title);
    lines.push("");
    lines.push("*" + quizLine(m.n) + "*");
    const section = document.getElementById("page-module-" + m.n);
    const fields = [...section.querySelectorAll("[data-store]")];
    let has = false;
    fields.forEach(el => {{
      const v = (el.value || "").trim();
      if (!v) return;
      has = true;
      lines.push("");
      lines.push("### " + fieldLabel(el));
      lines.push("");
      lines.push(v);
    }});
    if (!has) {{ lines.push(""); lines.push("_Артефакты пока не заполнены._"); }}
  }});
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("## Итоговый проект");
  document.querySelectorAll("#page-project [data-project-field]").forEach(el => {{
    const v = (el.value || "").trim();
    if (!v) return;
    lines.push("");
    lines.push("### " + fieldLabel(el));
    lines.push("");
    lines.push(v);
  }});
  lines.push("");
  lines.push("### Самооценка по рубрике");
  lines.push("");
  lines.push("| Критерий | Балл |");
  lines.push("|---|---:|");
  DATA.rubric.forEach(r => {{
    lines.push("| " + r.title + " | " + (state.rubric[r.key] ?? "—") + " |");
  }});
  lines.push("");
  lines.push("**Итого:** " + rubricTotal() + " из 16.");
  lines.push("");
  lines.push("---");
  lines.push("");
  lines.push("_Документ сформирован в онлайн-курсе «ИИ для образования». Проверьте персональные данные перед передачей файла._");
  return lines.join("\\n");
}}
function downloadPortfolio() {{
  downloadFile("portfolio-ai-education.md", buildPortfolio(), "text/markdown;charset=utf-8");
  showToast("Портфолио скачано в Markdown");
}}
function buildModuleMarkdown(n) {{
  const m = DATA.modules.find(x => x.n === Number(n));
  const section = document.getElementById("page-module-" + n);
  const lines = [];
  lines.push("# Модуль " + String(n).padStart(2, "0") + ". " + m.title);
  lines.push("");
  lines.push("**Участник:** " + (state.learner.name || "—"));
  lines.push("**Логин:** " + (currentUser || "—"));
  lines.push("**Дисциплина:** " + (state.learner.discipline || "—"));
  lines.push("**Дата:** " + new Date().toLocaleDateString("ru-RU"));
  lines.push("");
  lines.push("*" + quizLine(n) + "*");
  section.querySelectorAll("[data-store]").forEach(el => {{
    const v = (el.value || "").trim();
    if (!v) return;
    lines.push("");
    lines.push("## " + fieldLabel(el));
    lines.push("");
    lines.push(v);
  }});
  lines.push("");
  lines.push("---");
  lines.push("_Сформировано в курсе «ИИ для образования»._");
  return lines.join("\\n");
}}
function printHTML(title, body) {{
  const sheet = document.getElementById("print-sheet");
  if (!sheet) return;
  sheet.innerHTML = '<div class="print-doc"><h1>' + title + '</h1>' + body + '</div>';
  document.body.classList.add("printing-sheet");
  window.print();
  setTimeout(() => document.body.classList.remove("printing-sheet"), 800);
}}
function projectPrintBody() {{
  const lines = [];
  const who = [state.learner.name, state.learner.org, state.learner.discipline].filter(Boolean).join(" · ") || "Участник курса";
  lines.push('<div class="meta">' + escapeHTML(who) + ' · ' + new Date().toLocaleDateString("ru-RU") + '</div>');
  document.querySelectorAll("#page-project [data-project-field]").forEach(el => {{
    const v = (el.value || "").trim();
    if (!v) return;
    lines.push("<h3>" + escapeHTML(fieldLabel(el)) + "</h3><div class='answer'>" + escapeHTML(v) + "</div>");
  }});
  lines.push("<h2>Самооценка по рубрике</h2><table><thead><tr><th>Критерий</th><th>Балл</th></tr></thead><tbody>");
  DATA.rubric.forEach(r => {{
    lines.push("<tr><td>" + escapeHTML(r.title) + "</td><td>" + (state.rubric[r.key] ?? "—") + "</td></tr>");
  }});
  lines.push("</tbody></table><p><strong>Итого: " + rubricTotal() + " из 16.</strong></p>");
  return lines.join("");
}}
function escapeHTML(s) {{
  return String(s).replace(/[&<>"']/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[c]));
}}
function buildTemplates() {{
  const lines = ["# Шаблоны курса «ИИ для образования»", "", "## Карта применений", "", "1. Задача:", "   Что поручить ИИ:", "   Что проверить:", "", "2. Задача:", "   Что поручить ИИ:", "   Что проверить:", "", "## Рабочий запрос", "", "Ты — [роль]. Подготовь [тип материала] для студентов [курс, специальность, уровень].", "Тема: [тема].", "Цель: после выполнения студенты смогут [наблюдаемое действие].", "Условия: [время, формат работы, доступные материалы].", "Ответ представь в формате [структура].", "Не выдумывай факты. Если данных не хватает, сначала задай уточняющие вопросы.", "", "## Три версии задания", "", "Общая цель: [цель]", "", "Версия 1 — базовая:", "Версия 2 — стандартная:", "Версия 3 — повышенной сложности:", "", "## Критерии оценивания", "", "| Критерий | Высокий | Достаточный | Требует доработки |", "|---|---|---|---|", "|  |  |  |  |", "", "## Правила использования ИИ", "", "Для работы «[название]» использование ИИ: [разрешено / ограничено / не разрешено].", "Можно: ", "Нельзя: ", "Как сообщить: ", "Ответственность студента: ", "", "## Чек-лист безопасности", "", ...CHECKLIST_MD, "", "## Итоговый проект", "", ...PROJECT_MD];
  return lines.join("\\n");
}}
const CHECKLIST_MD = {json.dumps(["- [ ] " + x for x in CHECKLISTS["safety"]], ensure_ascii=False)};
const PROJECT_MD = {json.dumps(["- [ ] " + f["label"] for f in PROJECT_FIELDS], ensure_ascii=False)};

/* ---------- events ---------- */
document.addEventListener("click", e => {{
  const dl = e.target.closest("[data-download-portfolio]");
  if (dl) {{ downloadPortfolio(); return; }}
  const dm = e.target.closest("[data-download-module]");
  if (dm) {{
    downloadFile("module-" + dm.dataset.downloadModule + ".md", buildModuleMarkdown(dm.dataset.downloadModule), "text/markdown;charset=utf-8");
    showToast("Результат модуля скачан");
    return;
  }}
  const dp = e.target.closest("[data-download-project]");
  if (dp) {{
    downloadFile("project-ai-education.md", buildPortfolio().split("## Итоговый проект")[1] ? "# Итоговый проект\\n" + buildPortfolio().split("## Итоговый проект")[1] : buildPortfolio(), "text/markdown;charset=utf-8");
    showToast("Проект скачан");
    return;
  }}
  const tp = e.target.closest("[data-download-templates]");
  if (tp) {{ downloadFile("shablony-ai-education.md", buildTemplates(), "text/markdown;charset=utf-8"); showToast("Шаблоны скачаны"); return; }}
  const pp = e.target.closest("[data-print-project]");
  if (pp) {{ printHTML("Учебный сценарий", projectPrintBody()); return; }}
  const pc = e.target.closest("[data-print-certificate]");
  if (pc) {{
    const body = '<p>Курс «ИИ для образования» · 16 академических часов</p><h2>Лист завершения курса</h2><p>Участник: <strong>' + escapeHTML(state.learner.name || "—") + '</strong></p><p>Организация: ' + escapeHTML(state.learner.org || "—") + '</p><p>Дисциплина: ' + escapeHTML(state.learner.discipline || "—") + '</p><p>Пройдено модулей: ' + completedCount() + ' из 8. Самооценка проекта: ' + rubricTotal() + ' из 16.</p><p>Дата: ' + new Date().toLocaleDateString("ru-RU") + '</p><p><em>Документ самопроверки. Не заменяет официальный сертификат организации.</em></p>';
    printHTML("Лист завершения курса", body);
    return;
  }}
}});
document.addEventListener("click", e => {{
  const reset = e.target.closest("[data-reset-progress]");
  if (!reset) return;
  if (!confirm("Сбросить весь прогресс, ответы и проект? Это действие нельзя отменить.")) return;
  try {{ localStorage.removeItem(KEY); }} catch (err) {{}}
  location.reload();
}});

/* ---------- menu ---------- */
function closeSidebar() {{
  document.body.classList.remove("sidebar-open");
  const mb = document.getElementById("menu-btn");
  if (mb) mb.setAttribute("aria-expanded", "false");
}}
document.getElementById("menu-btn")?.addEventListener("click", () => {{
  document.body.classList.toggle("sidebar-open");
  const mb = document.getElementById("menu-btn");
  if (mb) mb.setAttribute("aria-expanded", document.body.classList.contains("sidebar-open") ? "true" : "false");
}});
document.querySelectorAll("[data-close-sidebar]").forEach(el => el.addEventListener("click", closeSidebar));
document.addEventListener("keydown", e => {{ if (e.key === "Escape") closeSidebar(); }});

/* ---------- auth / init ---------- */
function setUserLabels(login) {{
  document.querySelectorAll("[data-current-user]").forEach(el => el.textContent = login);
  const chip = document.getElementById("user-chip");
  if (chip) chip.hidden = false;
  const sb = document.getElementById("sidebar-user-box");
  if (sb) sb.hidden = false;
}}
function startCourse(login) {{
  currentUser = login;
  KEY = KEY_PREFIX + login;
  state = loadState();
  document.body.classList.remove("auth-locked");
  const app = document.querySelector(".app");
  if (app) app.hidden = false;
  const loginScreen = document.getElementById("login-screen");
  if (loginScreen) loginScreen.hidden = true;
  setUserLabels(login);
  if (!location.hash) {{
    if (state.lastRoute && document.getElementById("page-" + state.lastRoute)) location.hash = state.lastRoute;
    else if (window.SCORM) {{
      const savedRoute = window.SCORM.getLocation();
      if (savedRoute && document.getElementById("page-" + savedRoute)) location.hash = savedRoute;
    }}
  }}
  restoreFields();
  restoreQuizzes();
  restoreRubric();
  initChecklists();
  filterPrompts();
  updateProgress();
  updateRubric();
  updateProjectStatus();
  showRoute();
  if (!storageOK) showToast("Браузер не разрешает сохранение. Работайте без перезагрузки страницы.");
}}
function showLogin() {{
  document.body.classList.add("auth-locked");
  const app = document.querySelector(".app");
  if (app) app.hidden = true;
  const loginScreen = document.getElementById("login-screen");
  if (loginScreen) loginScreen.hidden = false;
  const chip = document.getElementById("user-chip");
  if (chip) chip.hidden = true;
  const sb = document.getElementById("sidebar-user-box");
  if (sb) sb.hidden = true;
  setTimeout(() => {{ const u = document.getElementById("login-user"); if (u) u.focus(); }}, 80);
}}
function logout() {{
  saveNow();
  if (AUTH) AUTH.logout();
  location.hash = "";
  location.reload();
}}
function bindLogin() {{
  const form = document.getElementById("login-form");
  if (!form) return;
  const userInput = document.getElementById("login-user");
  const passInput = document.getElementById("login-pass");
  const remember = document.getElementById("login-remember");
  const error = document.getElementById("login-error");
  const toggle = document.getElementById("toggle-pass");
  const forgot = document.getElementById("forgot-link");
  const submit = form.querySelector("button[type=submit]");
  if (toggle) toggle.addEventListener("click", () => {{
    const show = passInput.type === "password";
    passInput.type = show ? "text" : "password";
    toggle.textContent = show ? "Скрыть" : "Показать";
    toggle.setAttribute("aria-label", show ? "Скрыть пароль" : "Показать пароль");
    passInput.focus();
  }});
  if (forgot) forgot.addEventListener("click", () => {{
    if (error) error.textContent = "Обратитесь к преподавателю: он выдаст логин и пароль или заменит доступ.";
    showToast("Доступ выдаёт преподаватель");
  }});
  form.addEventListener("submit", async e => {{
    e.preventDefault();
    if (error) error.textContent = "";
    const loginName = (userInput.value || "").trim();
    const pwd = passInput.value || "";
    if (!loginName || !pwd) {{
      if (error) error.textContent = "Введите логин и пароль.";
      (loginName ? passInput : userInput).focus();
      return;
    }}
    const res = AUTH ? AUTH.login(loginName, pwd, !!(remember && remember.checked)) : {{ ok: false, reason: "storage" }};
    if (res.ok) {{
      if (submit) {{ submit.disabled = true; submit.textContent = "Вход…"; }}
      startCourse(res.login);
      return;
    }}
    if (res.reason === "locked") {{
      if (error) error.textContent = "Слишком много попыток. Подождите " + (res.wait || 30) + " секунд и попробуйте снова.";
    }} else if (res.reason === "invalid") {{
      if (error) error.textContent = "Неверный логин или пароль." + (res.left ? (" Осталось попыток: " + res.left + ".") : "");
      passInput.value = "";
      passInput.focus();
    }} else if (res.reason === "storage") {{
      if (error) error.textContent = "Браузер не разрешает сохранить вход. Откройте курс через http/https или разрешите localStorage.";
    }} else if (res.reason === "empty") {{
      if (error) error.textContent = "Введите логин и пароль.";
    }} else {{
      if (error) error.textContent = "Не удалось выполнить вход. Попробуйте ещё раз.";
    }}
  }});
}}
document.getElementById("logout-btn")?.addEventListener("click", logout);
document.getElementById("logout-btn-side")?.addEventListener("click", logout);
bindLogin();
const savedAuth = AUTH ? AUTH.current() : null;
if (savedAuth) startCourse(savedAuth.login); else showLogin();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    from pathlib import Path
    Path("index.html").write_text(build_html(), encoding="utf-8")
    print("index.html:", len(build_html()), "bytes")
