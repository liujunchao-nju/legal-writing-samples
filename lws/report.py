"""Markdown 与 HTML 渲染：写作大纲、要素校验报告、范文导出。

所有渲染都支持可选的 `party` 立场参数，用于在大纲与报告中给出立场提示。
HTML 产物为单文件、内联样式、无任何外部引用，可离线双击打开。
"""

from __future__ import annotations

from .documents import check_document, load_document
from .laws import format_law, load_laws

_PARTY_LABELS = {
    "原告": "原告", "被告": "被告", "上诉人": "上诉人", "被上诉人": "被上诉人",
    "申请人": "申请人", "被申请人": "被申请人", "辩护人": "辩护人", "再审申请人": "再审申请人",
}


def _party_text(party: str | None) -> str:
    if not party:
        return ""
    return _PARTY_LABELS.get(party, party)


def _party_note(doc: dict, party: str | None) -> str:
    if not party:
        return ""
    notes = doc.get("party_notes") or {}
    return " ".join(str(notes.get(party, "")).split())


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------

def render_outline(doc_type: str, party: str | None = None) -> str:
    """把一类文书的骨架渲染成可直接填写的写作大纲。"""
    doc = load_document(doc_type)
    index = load_laws()
    p = _party_text(party)

    lines = [f"# {doc['label']} · 写作大纲", ""]
    if p:
        lines.append(f"- 立场视角：{p}")
    lines.append(f"- 文书类型标识：`{doc['type']}`")
    if doc.get("category"):
        lines.append(f"- 分类：{doc['category']}")
    if doc.get("usage"):
        lines.append(f"- 适用场景：{' '.join(str(doc['usage']).split())}")
    basis = doc.get("legal_basis") or []
    if basis:
        lines.append("- 主要依据：")
        for key in basis:
            record = index.get(key)
            if record:
                lines.append(f"  - {format_law(key, index)}")
            else:
                lines.append(f"  - {key}（未核验）")
    note = _party_note(doc, party)
    if note:
        lines.append("")
        lines.append(f"> 立场提示（{p}）：{note}")
    lines.append("")

    lines.append("## 一、结构顺序")
    lines.append("")
    for i, item in enumerate(doc.get("structure") or [], start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 二、要素清单")
    lines.append("")
    lines.append("| 要素 | 必备 | 命中关键词 | 立场侧重 | 说明 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for element in doc["elements"]:
        must = "是" if element.get("required") else ""
        keywords = "、".join(element.get("keywords") or [])
        enote = " ".join(str(element.get("note") or "").split())
        plist = element.get("parties") or []
        pmark = "、".join(_PARTY_LABELS.get(x, x) for x in plist) if plist else ""
        lines.append(f"| {element['label']} | {must} | {keywords} | {pmark} | {enote} |")
    lines.append("")

    tips = doc.get("tips") or []
    if tips:
        lines.append("## 三、写作要点")
        lines.append("")
        for tip in tips:
            lines.append(f"- {' '.join(str(tip).split())}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_check(result: dict, party: str | None = None) -> str:
    """渲染要素校验报告（Markdown）。"""
    p = _party_text(party)
    lines = [f"# {result['label']} 要素校验", ""]
    if p:
        lines.append(f"- 立场视角：{p}")
    lines.append(f"- 文书类型：`{result['type']}`")
    lines.append(f"- 必备要素：{result['total_required']} 项")
    lines.append(f"- 齐备率：{result['coverage']}%")
    lines.append(f"- 结论：{'要素齐备' if result['complete'] else '存在缺失，需补充'}")
    note = result.get("party_note")
    if note:
        lines.append("")
        lines.append(f"> 立场提示（{p}）：{' '.join(str(note).split())}")
    lines.append("")

    lines.append("## 缺失的必备要素")
    lines.append("")
    if result["missing_required"]:
        for element in result["missing_required"]:
            lines.append(f"- **{element['label']}**：{' '.join(str(element.get('note') or '').split())}")
    else:
        lines.append("无。")
    lines.append("")

    if result["missing_optional"]:
        lines.append("## 未出现的可选要素")
        lines.append("")
        for element in result["missing_optional"]:
            lines.append(f"- {element['label']}")
        lines.append("")

    lines.append("## 已命中的要素")
    lines.append("")
    for element in result["present"]:
        lines.append(f"- {element['label']}（命中：{'、'.join(element['matched'])}）")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_sample(sample: dict) -> str:
    """渲染一篇范文，把参照案例信息置于正文之前。"""
    ref = sample.get("reference") or {}
    lines = [f"# {sample.get('title', '')}", ""]
    lines.append("## 参照原文")
    lines.append("")
    if ref.get("case_id"):
        lines.append(f"- 案例编号：{ref['case_id']}")
    lines.append(f"- 案件名称：{ref.get('case_name', '')}")
    lines.append(f"- 来源：{ref.get('source', '')}")
    if ref.get("original_cause"):
        lines.append(f"- 案由：{ref['original_cause']}")
    if ref.get("original_forum"):
        lines.append(f"- 原审法院：{ref['original_forum']}")
    if ref.get("notes"):
        lines.append(f"- 改写说明：{' '.join(str(ref['notes']).split())}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(sample["_body"])
    return "\n".join(lines).rstrip() + "\n"


def format_check(result: dict) -> str:
    """终端可读的校验结论。"""
    lines = [
        f"文书类型：{result['label']}（{result['type']}）",
        f"必备要素 {result['total_required']} 项，齐备率 {result['coverage']}%",
    ]
    if result["missing_required"]:
        lines.append("")
        lines.append(f"缺失必备要素（{len(result['missing_required'])} 项）：")
        for element in result["missing_required"]:
            lines.append(f"  - {element['label']}")
    else:
        lines.append("")
        lines.append("全部必备要素已出现。")
    if result["missing_optional"]:
        lines.append("")
        lines.append(f"未出现的可选要素（{len(result['missing_optional'])} 项）：")
        for element in result["missing_optional"]:
            lines.append(f"  - {element['label']}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# HTML（单文件、内联样式、无任何外部引用，可离线打开）
# --------------------------------------------------------------------------

_CSS = """
:root {
  --bg: #f7f8fa; --card: #ffffff; --ink: #1f2329; --sub: #6b7280;
  --line: #e5e7eb; --red: #d92d20; --amber: #f79009; --green: #12b76a;
  --brand: #2f5fe0; --brand-soft: #eef2ff;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.7; padding: 28px 18px; }
.wrap { max-width: 860px; margin: 0 auto; }
h1 { font-size: 24px; margin: 0 0 4px; }
h2 { font-size: 18px; margin: 26px 0 10px; border-left: 4px solid var(--brand);
  padding-left: 10px; }
.meta { color: var(--sub); font-size: 13px; margin-bottom: 6px; }
.party { background: var(--brand-soft); color: var(--brand); border: 1px solid #c7d2fe;
  border-radius: 8px; padding: 10px 14px; font-size: 14px; margin: 12px 0; }
ol.struct { padding-left: 20px; }
ol.struct li { margin: 4px 0; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 4px; font-size: 13.5px; }
th, td { border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #f1f3f9; font-weight: 600; }
.badge { display: inline-block; min-width: 30px; text-align: center; border-radius: 999px;
  padding: 1px 8px; font-size: 12px; font-weight: 600; }
.b-required { background: #fee4e2; color: var(--red); }
.b-optional { background: #f2f4f7; color: var(--sub); }
.tips li { margin: 4px 0; }
.metric { display: flex; align-items: center; gap: 14px; background: var(--card);
  border: 1px solid var(--line); border-radius: 10px; padding: 14px 18px; margin: 10px 0; }
.metric .num { font-size: 30px; font-weight: 700; color: var(--brand); }
.bar { flex: 1; height: 12px; background: #eef0f4; border-radius: 999px; overflow: hidden; }
.bar > i { display: block; height: 100%; background: linear-gradient(90deg,#2f5fe0,#12b76a); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 12px 16px; margin: 10px 0; }
.card.red { border-left: 4px solid var(--red); }
.card.amber { border-left: 4px solid var(--amber); }
.card.green { border-left: 4px solid var(--green); }
.tag { font-size: 12px; font-weight: 600; padding: 1px 8px; border-radius: 6px; }
.tag.red { background: #fee4e2; color: var(--red); }
.tag.amber { background: #fef0c7; color: var(--amber); }
.tag.green { background: #d1fadf; color: var(--green); }
.foot { color: var(--sub); font-size: 12px; margin-top: 30px; border-top: 1px solid var(--line); padding-top: 10px; }
"""


def render_outline_html(doc_type: str, party: str | None = None) -> str:
    doc = load_document(doc_type)
    index = load_laws()
    p = _party_text(party)
    basis_rows = ""
    for key in doc.get("legal_basis") or []:
        record = index.get(key)
        if record:
            basis_rows += f"<li>{_esc(format_law(key, index))}</li>"
        else:
            basis_rows += f"<li>{_esc(key)}（未核验）</li>"
    struct_rows = "".join(f"<li>{_esc(s)}</li>" for s in (doc.get("structure") or []))

    elem_rows = ""
    for e in doc["elements"]:
        must = e.get("required")
        badge = '<span class="badge b-required">必备</span>' if must else '<span class="badge b-optional">可选</span>'
        kw = "、".join(e.get("keywords") or [])
        plist = e.get("parties") or []
        pmark = "、".join(_PARTY_LABELS.get(x, x) for x in plist) if plist else "—"
        note = " ".join(str(e.get("note") or "").split())
        elem_rows += (
            f"<tr><td>{_esc(e['label'])}</td><td>{badge}</td>"
            f"<td>{_esc(kw)}</td><td>{_esc(pmark)}</td><td>{_esc(note)}</td></tr>"
        )
    tips_rows = "".join(f"<li>{_esc(' '.join(str(t).split()))}</li>" for t in (doc.get("tips") or []))
    party_html = ""
    note = _party_note(doc, party)
    if p:
        party_html = f'<div class="party"><strong>立场视角：{_esc(p)}</strong>'
        if note:
            party_html += f"　{note}"
        party_html += "</div>"

    body = f"""
<div class="wrap">
  <h1>{_esc(doc['label'])} · 写作大纲</h1>
  <div class="meta">文书类型标识：<code>{_esc(doc['type'])}</code>
  ｜ 分类：{_esc(doc.get('category',''))}
  ｜ 适用：{_esc(' '.join(str(doc.get('usage') or '').split()))}</div>
  {party_html}
  <h2>主要依据</h2>
  <ul>{basis_rows}</ul>
  <h2>一、结构顺序</h2>
  <ol class="struct">{struct_rows}</ol>
  <h2>二、要素清单</h2>
  <table>
    <thead><tr><th>要素</th><th>必备</th><th>命中关键词</th><th>立场侧重</th><th>说明</th></tr></thead>
    <tbody>{elem_rows}</tbody>
  </table>
  <h2>三、写作要点</h2>
  <ul class="tips">{tips_rows}</ul>
  <div class="foot">由 lws（legal-writing-samples）生成 · 法定条号以经核验法条库为准 · 本大纲不构成法律意见</div>
</div>
"""
    return _HTML_DOC.format(title=f"{doc['label']} 写作大纲", css=_CSS, body=body)


def render_check_html(result: dict, party: str | None = None) -> str:
    p = _party_text(party)
    cov = result.get("coverage", 0)
    party_html = ""
    if p:
        party_html = f'<div class="party"><strong>立场视角：{_esc(p)}</strong>'
        note = result.get("party_note")
        if note:
            party_html += f"　{_esc(' '.join(str(note).split()))}"
        party_html += "</div>"

    miss_req = result["missing_required"]
    miss_opt = result["missing_optional"]
    present = result["present"]

    cards = ""
    for e in miss_req:
        cards += (f'<div class="card red"><span class="tag red">缺失·必备</span> '
                  f'<strong>{_esc(e["label"])}</strong>'
                  f'<div>{_esc(" ".join(str(e.get("note") or "").split()))}</div></div>')
    for e in miss_opt:
        cards += (f'<div class="card amber"><span class="tag amber">未出现·可选</span> '
                  f'<strong>{_esc(e["label"])}</strong></div>')
    for e in present:
        cards += (f'<div class="card green"><span class="tag green">已命中</span> '
                  f'<strong>{_esc(e["label"])}</strong>'
                  f'<div>命中关键词：{_esc("、".join(e.get("matched", [])))}</div></div>')

    conclusion = "要素齐备" if result["complete"] else "存在缺失，需补充"
    body = f"""
<div class="wrap">
  <h1>{_esc(result['label'])} · 要素校验报告</h1>
  <div class="meta">文书类型：<code>{_esc(result['type'])}</code>
  ｜ 必备要素 {result['total_required']} 项
  ｜ 结论：{_esc(conclusion)}</div>
  {party_html}
  <div class="metric">
    <div class="num">{cov}%</div>
    <div style="flex:1">
      <div>必备要素齐备率</div>
      <div class="bar"><i style="width:{cov}%"></i></div>
    </div>
  </div>
  {cards}
  <div class="foot">由 lws（legal-writing-samples）生成 · 校验仅做提醒、不判分，关键词未命中可能只是换了表述 · 本报告不构成法律意见</div>
</div>
"""
    return _HTML_DOC.format(title=f"{result['label']} 要素校验", css=_CSS, body=body)


_HTML_DOC = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>{body}</body>
</html>"""


def _esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


__all__ = [
    "render_outline", "render_outline_html", "render_check", "render_check_html",
    "render_sample", "format_check", "check_document",
]
