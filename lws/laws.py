"""法条库：加载经核验的条文，并提供条号提取与校验。

本模块承担两件事：
1. 文书要素里的 basis 引用必须以 key 形式命中 laws.yaml；
2. 范文正文里以汉字写成的条号（如「第五百七十七条」），必须能在 laws.yaml 中找到对应条文。

第二项是刻意做的：范文里的条号是最容易被改错又最难被发现的地方，
把它纳入自动校验，改错条号会让测试直接失败。
"""

from __future__ import annotations

import pathlib
import re

import yaml

DATA_DIR = pathlib.Path(__file__).parent / "data"
LAWS_FILE = DATA_DIR / "laws.yaml"
DOCUMENTS_DIR = DATA_DIR / "documents"
SAMPLES_DIR = DATA_DIR / "samples"

_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_UNITS = {"十": 10, "百": 100, "千": 1000}

# 法律名称与条号分开匹配。
# 书名号内出现「合同、协议、章程、条约、公约、办法、细则」等字样的，视为合同或协议条款引用，
# 不计入法条校验，以免把「《商品房预售合同》第三十条」误判为法条。
_LAW_NAME_RE = re.compile(
    r"《(?![^》]*(?:合同|协议|章程|条约|公约|办法|细则))[^》]{2,40}》"
)
_ARTICLE_RE = re.compile(r"第([零一二三四五六七八九十百千]+)条")
_STOP_CHARS = "。；;！？\n"


class LawError(ValueError):
    """法条库或引用不合法。"""


def cn_to_int(text: str) -> int:
    """把汉字数字转换为整数，支持到千位。"""
    section = 0
    number = 0
    for ch in text:
        if ch in _CN_DIGITS:
            number = _CN_DIGITS[ch]
        elif ch in _CN_UNITS:
            unit = _CN_UNITS[ch]
            if number == 0:
                number = 1
            section += number * unit
            number = 0
        else:
            raise ValueError(f"无法识别的汉字数字: {text}")
    return section + number


def int_to_cn(value: int) -> str:
    """把整数转成汉字写法，用于展示与比对。"""
    digits = "零一二三四五六七八九"
    if value < 10:
        return digits[value]
    if value < 20:
        return "十" + (digits[value % 10] if value % 10 else "")
    if value < 100:
        return digits[value // 10] + "十" + (digits[value % 10] if value % 10 else "")
    if value < 1000:
        head = digits[value // 100] + "百"
        rest = value % 100
        if rest == 0:
            return head
        if rest < 10:
            return head + "零" + digits[rest]
        return head + int_to_cn(rest)
    raise ValueError(f"暂不支持四位以上: {value}")


def load_laws() -> dict:
    """读取法条库，返回 {key: 记录}。"""
    with LAWS_FILE.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict) or "laws" not in doc:
        raise LawError(f"{LAWS_FILE.name} 结构不合法：缺少 laws 字段")
    index: dict[str, dict] = {}
    for record in doc["laws"]:
        for field in ("key", "law", "article", "title", "text"):
            if not record.get(field):
                raise LawError(f"{LAWS_FILE.name} 中有一条记录缺少 {field}: {record}")
        key = record["key"]
        if key in index:
            raise LawError(f"{LAWS_FILE.name} 中存在重复 key: {key}")
        index[key] = record
    if not index:
        raise LawError(f"{LAWS_FILE.name} 中没有任何法条")
    return index


def meta() -> dict:
    """返回法条库的元信息。"""
    with LAWS_FILE.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return {
        "verified_on": doc.get("verified_on", ""),
        "verified_by": doc.get("verified_by", ""),
        "count": len(doc.get("laws", [])),
    }


def look_up(key: str, index: dict | None = None) -> dict:
    """按 key 取回一条法条。"""
    index = index if index is not None else load_laws()
    if key not in index:
        raise LawError(f"引用了未核验的法条: {key}")
    return index[key]


def verify_references(keys, index: dict | None = None) -> list[str]:
    """检查一批 key 是否都在白名单内，返回未核验的列表。"""
    index = index if index is not None else load_laws()
    return [k for k in keys if k not in index]


def known_articles() -> set[int]:
    """返回法条库中出现过的全部条号。"""
    return {int(record["article"]) for record in load_laws().values()}


def cited_articles(text: str) -> set[int]:
    """从文本中提取紧跟法律名称之后的条号，支持并列写法（如「第一百二十二条、第一百二十四条」）。"""
    numbers: set[int] = set()
    for match in _LAW_NAME_RE.finditer(text):
        tail = text[match.end():]
        stops = [len(tail)]
        for ch in _STOP_CHARS:
            idx = tail.find(ch)
            if idx != -1:
                stops.append(idx)
        idx = tail.find("《")
        if idx != -1:
            stops.append(idx)
        segment = tail[: min(stops)]
        for article in _ARTICLE_RE.finditer(segment):
            try:
                numbers.add(cn_to_int(article.group(1)))
            except ValueError:
                continue
    return numbers


def unknown_articles(text: str, index: dict | None = None) -> list[int]:
    """返回文本中引用但未在法条库登记过的条号。"""
    return sorted(cited_articles(text) - known_articles())


def format_law(key: str, index: dict | None = None) -> str:
    """把 key 渲染成便于阅读的引用说明。"""
    record = look_up(key, index)
    return f"{record['law']}第{int_to_cn(int(record['article']))}条（{record['title']}，{record['effective_from']} 施行）"
