"""Markdown 渲染：写作大纲、要素校验报告、范文导出。"""

from __future__ import annotations

from .documents import check_document, load_document
from .laws import format_law, load_laws


def render_outline(doc_type: str) -> str:
    """把一类文书的骨架渲染成可直接填写的写作大纲。"""
    doc = load_document(doc_type)
    index = load_laws()

    lines = [f"# {doc['label']} · 写作大纲", ""]
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
    lines.append("")

    lines.append("## 一、结构顺序")
    lines.append("")
    for i, item in enumerate(doc.get("structure") or [], start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 二、要素清单")
    lines.append("")
    lines.append("| 要素 | 必备 | 命中关键词 | 说明 |")
    lines.append("| --- | --- | --- | --- |")
    for element in doc["elements"]:
        must = "是" if element.get("required") else ""
        keywords = "、".join(element.get("keywords") or [])
        note = " ".join(str(element.get("note") or "").split())
        lines.append(f"| {element['label']} | {must} | {keywords} | {note} |")
    lines.append("")

    tips = doc.get("tips") or []
    if tips:
        lines.append("## 三、写作要点")
        lines.append("")
        for tip in tips:
            lines.append(f"- {' '.join(str(tip).split())}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_check(result: dict) -> str:
    """渲染要素校验报告。"""
    lines = [f"# {result['label']} 要素校验", ""]
    lines.append(f"- 文书类型：`{result['type']}`")
    lines.append(f"- 必备要素：{result['total_required']} 项")
    lines.append(f"- 齐备率：{result['coverage']}%")
    lines.append(f"- 结论：{'要素齐备' if result['complete'] else '存在缺失，需补充'}")
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


__all__ = ["render_outline", "render_check", "render_sample", "format_check", "check_document"]
