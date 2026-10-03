from __future__ import annotations
from html import escape

DIMENSIONS = [
    ("d1", "Does the code run without basic mistakes?", "D1", "teal"),
    ("d2", "Is the logic actually correct?", "D2", "teal"),
    ("d3", "How good is the written explanation?", "D3", "amber"),
    ("d4", "Does the explanation match the code?", "D4", "steel"),
    ("d5", "Did they go beyond what was asked?", "D5", "teal"),
]

def _items(value) -> list:
    if value is None: return []
    return value if isinstance(value, list) else [value]

def _text(item) -> str:
    if isinstance(item, dict):
        text = escape(str(item.get("text", "")))
        evidence = item.get("evidence")
        if evidence: text += f' <span class="cite">({escape(str(evidence))})</span>'
        return text
    return escape(str(item))

def _list(items: list, dot: str = "teal") -> str:
    if not items: items = ["No specific finding was recorded for this dimension."]
    return "<ul>" + "".join(f'<li><span class="dot {dot}"></span><span>{_text(item)}</span></li>' for item in items) + "</ul>"

def _grade(marks) -> str:
    try:
        score = float(marks)
    except (TypeError, ValueError):
        return "—"
    if not 0 <= score <= 100:
        return "—"
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"

def render_report(data: dict) -> str:
    sid = escape(str(data.get("student_id", "Student")))
    dims = "".join(f'<section class="dim"><h2>{title}<span class="tag">{tag}</span></h2>{_list(_items(data.get(key)), color)}</section>' for key, title, tag, color in DIMENSIONS)
    submitted = data.get("submitted_count", "—")
    marks = data.get("marks_awarded")
    explanations = data.get("explanation_count", "—")
    marks_display = f"{float(marks):g}/100" if isinstance(marks, (int, float)) and 0 <= marks <= 100 else "—"
    grade = _grade(marks)
    facts = [(submitted, "Programs submitted"), (marks_display, "Marks awarded"), (grade, "Grade"), (explanations, "Code explanations written")]
    fact_html = "".join(f'<div class="fact"><span class="n">{escape(str(n))}</span><span class="l">{label}</span></div>' for n, label in facts)
    dbl = _items(data.get("double_check")); support = _items(data.get("reinforce_basics")); stretch = _items(data.get("room_to_grow"))
    course = escape(str(data.get("course", "C Programming Lab"))); week = escape(str(data.get("week", "Week 4"))); topic = escape(str(data.get("topic", "Functions & Recursion")))
    authenticity = _list(dbl, "rose")
    support_html = "<ul>" + "".join(f"<li>{_text(x)}</li>" for x in support) + "</ul>" if support else "<p>No specific reinforcement identified.</p>"
    stretch_html = "<ul>" + "".join(f"<li>{_text(x)}</li>" for x in stretch) + "</ul>" if stretch else "<p>No specific extension identified.</p>"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lab Notebook Brief — {sid}</title>
<style>
:root{{--paper:#f5f6f3;--raised:#fff;--ink:#1b2430;--soft:#4b5563;--faint:#7c8794;--rule:#d7dcd7;--accent:#2e6f6e;--amber:#a5691e;--steel:#3b5ba5;--rose:#a1443f}}*{{box-sizing:border-box}}body{{margin:0;padding:40px 20px 64px;background:var(--paper);color:var(--ink);font:15px/1.55 'Segoe UI',sans-serif}}.sheet{{max-width:720px;margin:auto;background:var(--raised);border:1px solid var(--rule);padding:42px 50px;box-shadow:0 1px 2px #0001}}.letterhead{{display:flex;justify-content:space-between;align-items:end;border-bottom:2px solid var(--ink);padding-bottom:14px}}h1,h2{{font-family:Georgia,serif}}h1{{font-size:1.55rem;margin:0}}.sub,.meta{{color:var(--soft);font-size:.83rem}}.meta{{text-align:right;font-family:monospace;font-size:.72rem}}.factshead{{font-size:.8rem;text-transform:uppercase;letter-spacing:.07em;color:var(--faint);margin:22px 0 8px}}.factbar{{display:flex;border:1px solid var(--rule)}}.fact{{flex:1;padding:10px 12px;background:var(--paper);border-right:1px solid var(--rule)}}.fact:last-child{{border:0}}.n{{display:block;font:bold 1.1rem monospace;color:var(--accent)}}.l{{font-size:.65rem;text-transform:uppercase;color:var(--faint)}}.dim{{margin-top:28px;break-inside:avoid}}.dim h2,.authcard h2{{font-size:1.05rem;margin:0 0 11px;padding-bottom:7px;border-bottom:1px solid var(--rule)}}.tag{{font:600 .65rem monospace;color:var(--accent);margin-left:8px}}ul{{margin:0;padding:0;list-style:none}}li{{display:flex;gap:10px;margin:0 0 10px;line-height:1.6}}.dot{{width:8px;height:8px;border-radius:50%;margin-top:7px;flex:none;background:var(--accent)}}.dot.amber{{background:var(--amber)}}.dot.steel{{background:var(--steel)}}.dot.rose{{background:var(--rose)}}.cite{{font: .78rem monospace;color:var(--faint)}}.authcard{{margin-top:28px;border:1px solid var(--rose);background:#f6e6e4;padding:16px 20px}}.authcard h2{{color:var(--rose);border:0}}.lenses{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:28px}}.lens{{padding:14px 16px;background:#f5ead9}}.lens.stretch{{background:#e6eaf5}}.lens h3{{font:600 .9rem Georgia;margin:0 0 8px;color:var(--amber)}}.lens.stretch h3{{color:var(--steel)}}.lens li{{font-size:.84rem}}.disclaimer{{margin-top:26px;padding-top:14px;border-top:1px dashed #b9c1ba;font-size:.78rem;color:var(--faint);font-style:italic}}.footline{{display:flex;justify-content:space-between;margin-top:12px;font: .65rem monospace;color:var(--faint)}}@media(max-width:640px){{body{{padding:14px}}.sheet{{padding:24px 20px}}.letterhead{{display:block}}.meta{{text-align:left;margin-top:8px}}.factbar{{flex-wrap:wrap}}.fact{{flex:1 1 45%}}.lenses{{grid-template-columns:1fr}}}}@media print{{body{{padding:0;background:white}}.sheet{{border:0;box-shadow:none;max-width:none;padding:8mm 10mm}}}}
</style></head><body><main class="sheet"><header class="letterhead"><div><h1>Lab Notebook Brief</h1><div class="sub">{escape(str(data.get("week", "Week 4")))} · {topic} · {course}</div></div><div class="meta">Student {sid}<br>{escape(str(data.get("report_date", "Advisory report")))}</div></header>
<h2 class="factshead">Submission at a glance</h2><div class="factbar">{fact_html}</div>{dims}
<section class="authcard"><h2>Anything worth double-checking in person? <span class="tag">Not a score</span></h2>{authenticity}</section>
<section class="lenses"><div class="lens"><h3>If reinforcing basics</h3>{support_html}</div><div class="lens stretch"><h3>If looking for room to grow</h3>{stretch_html}</div></section>
<div class="disclaimer">Marks reflect only the submitted code and notebook evidence. Attendance, effort, and how this student comes across in class are things only you can see — review the suggested grade in that context.</div><div class="footline"><span>{escape(str(data.get("section", "")))} · {week}</span><span>AI-assisted grade · review recommended</span></div></main></body></html>'''
