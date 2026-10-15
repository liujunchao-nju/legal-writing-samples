"""范文：加载带来源标注的范文，并校验其条号引用与来源信息。

每篇范文都以 YAML front matter 标注参照的公开案例（入库编号或指导性案例编号、
案件名称、来源、原审法院），正文里出现的法条条号会被拿去与法条库比对，
出现未登记的条号即报错。
"""

from __future__ import annotations

import pathlib

import yaml

from .laws import SAMPLES_DIR, unknown_articles
from .documents import list_documents

REQUIRED_META = ("type", "title", "reference")
REQUIRED_REFERENCE = ("case_name", "source")


class SampleError(ValueError):
    """范文文件不合法。"""


def _split_front_matter(path: pathlib.Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.lstrip().startswith("---"):
        raise SampleError(f"{path.name} 缺少 YAML front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SampleError(f"{path.name} 的 front matter 未闭合")
    meta = yaml.safe_load(parts[1])
    if not isinstance(meta, dict):
        raise SampleError(f"{path.name} 的 front matter 必须是映射")
    return meta, parts[2].strip()


def list_samples() -> list[dict]:
    """列出全部范文，按文件名排序（文件名前缀即展示序号）。"""
    samples: list[dict] = []
    for path in sorted(SAMPLES_DIR.glob("*.md")):
        meta, body = _split_front_matter(path)
        meta["_file"] = path.name
        meta["_slug"] = path.stem
        meta["_body"] = body
        samples.append(meta)
    return samples


def load_sample(key: str) -> dict:
    """按文件名或序号前缀加载范文，例如 '01' 或 '01-complaint-sales'。"""
    samples = list_samples()
    for sample in samples:
        if sample["_slug"] == key or sample["_file"] == key:
            return sample
    matches = [s for s in samples if s["_slug"].startswith(key)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise KeyError(f"前缀 {key} 命中多篇范文，请写全")
    available = ", ".join(s["_slug"] for s in samples)
    raise KeyError(f"未找到范文: {key}；可用: {available}")


def validate_all() -> list[str]:
    """校验全部范文，返回其 slug 列表。"""
    known_types = {d["type"] for d in list_documents()}
    slugs: list[str] = []
    for path in sorted(SAMPLES_DIR.glob("*.md")):
        meta, body = _split_front_matter(path)

        missing = [k for k in REQUIRED_META if not meta.get(k)]
        if missing:
            raise SampleError(f"{path.name} 缺少字段: {', '.join(missing)}")

        if meta["type"] not in known_types:
            raise SampleError(f"{path.name} 的 type「{meta['type']}」没有对应的文书类型定义")

        reference = meta["reference"]
        if not isinstance(reference, dict):
            raise SampleError(f"{path.name} 的 reference 必须是映射")
        lack = [k for k in REQUIRED_REFERENCE if not reference.get(k)]
        if lack:
            raise SampleError(f"{path.name} 的 reference 缺少字段: {', '.join(lack)}")

        unknown = unknown_articles(body)
        if unknown:
            raise SampleError(f"{path.name} 引用了未核验的条号: {unknown}")

        slugs.append(path.stem)
    if not slugs:
        raise SampleError(f"没有找到任何范文: {SAMPLES_DIR}")
    return slugs


def list_by_type(doc_type: str) -> list[dict]:
    """返回某一文书类型下的全部范文。"""
    return [s for s in list_samples() if s.get("type") == doc_type]
