"""文书类型：加载要素模型、生成写作大纲、校验文书要素。

规则写在 data/documents/*.yaml，本模块只负责读取、校验与使用。
新增一类文书不需要改代码，放一个 YAML 文件即可。
"""

from __future__ import annotations

import pathlib

import yaml

from .laws import DOCUMENTS_DIR, load_laws, verify_references

REQUIRED_TOP = ("type", "label")
REQUIRED_ELEMENT = ("id", "label")


class DocumentError(ValueError):
    """文书类型定义不合法。"""


def _read(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise DocumentError(f"{path.name} 内容必须是映射")
    return doc


def _iter_basis(node) -> list[str]:
    """递归收集文档中所有 basis 引用。"""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "basis" and isinstance(value, list):
                found.extend(str(v) for v in value)
            else:
                found.extend(_iter_basis(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_iter_basis(item))
    return found


def _validate(doc: dict, path: pathlib.Path, law_index: dict) -> None:
    missing = [k for k in REQUIRED_TOP if not doc.get(k)]
    if missing:
        raise DocumentError(f"{path.name} 缺少必要字段: {', '.join(missing)}")

    elements = doc.get("elements")
    if not isinstance(elements, list) or not elements:
        raise DocumentError(f"{path.name} 的 elements 必须是非空列表")

    seen: set[str] = set()
    for element in elements:
        lack = [k for k in REQUIRED_ELEMENT if not element.get(k)]
        if lack:
            raise DocumentError(f"{path.name} 中有一条要素缺少 {', '.join(lack)}: {element}")
        if element["id"] in seen:
            raise DocumentError(f"{path.name} 中要素 id 重复: {element['id']}")
        seen.add(element["id"])
        if not element.get("keywords"):
            raise DocumentError(f"{path.name} 的要素「{element['label']}」缺少 keywords，无法校验")

    if not any(e.get("required") for e in elements):
        raise DocumentError(f"{path.name} 没有任何必备要素")

    unknown = verify_references(_iter_basis(doc), law_index)
    if unknown:
        raise DocumentError(f"{path.name} 引用了未核验的法条: {', '.join(sorted(set(unknown)))}")


def list_documents() -> list[dict]:
    """列出全部文书类型，按 type 排序。"""
    docs: list[dict] = []
    for path in sorted(DOCUMENTS_DIR.glob("*.yaml")):
        doc = _read(path)
        doc["_file"] = path.name
        docs.append(doc)
    return sorted(docs, key=lambda d: d.get("type", ""))


def load_document(doc_type: str) -> dict:
    """按 type 加载一类文书。"""
    for doc in list_documents():
        if doc.get("type") == doc_type:
            return doc
    available = ", ".join(d.get("type", "?") for d in list_documents())
    raise KeyError(f"未知的文书类型: {doc_type}；可用: {available}")


def validate_all() -> list[str]:
    """校验全部文书类型定义，返回类型名列表。"""
    law_index = load_laws()
    names: list[str] = []
    for path in sorted(DOCUMENTS_DIR.glob("*.yaml")):
        doc = _read(path)
        _validate(doc, path, law_index)
        names.append(doc["type"])
    if not names:
        raise DocumentError(f"没有找到任何文书类型: {DOCUMENTS_DIR}")
    return names


def _normalize(text: str) -> str:
    """去掉空白字符，避免换行与空格造成漏配。"""
    return "".join(text.split())


def check_document(doc_type: str, text: str) -> dict:
    """对照要素模型校验一份文书，返回齐备与缺失情况。"""
    doc = load_document(doc_type)
    body = _normalize(text)

    present: list[dict] = []
    missing_required: list[dict] = []
    missing_optional: list[dict] = []
    for element in doc["elements"]:
        hit = [kw for kw in element["keywords"] if _normalize(kw) in body]
        if hit:
            present.append({**element, "matched": hit})
        elif element.get("required"):
            missing_required.append(element)
        else:
            missing_optional.append(element)

    total_required = sum(1 for e in doc["elements"] if e.get("required"))
    hit_required = total_required - len(missing_required)
    coverage = round(hit_required / total_required * 100, 1) if total_required else 0.0
    return {
        "type": doc["type"],
        "label": doc["label"],
        "total_required": total_required,
        "present": present,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "coverage": coverage,
        "complete": not missing_required,
    }
