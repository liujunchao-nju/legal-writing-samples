"""法律文书范文库。

把法律文书的写作要求拆成可加载的规则与可复用的代码：
  - data/documents/*.yaml  各类文书的要素模型（依据、结构、必备要素、写作要点）
  - data/samples/*.md      基于公开案例改写的范文，逐篇标注参照案号
  - data/laws.yaml         经逐条核验的法条库（引用白名单）

对外 API：
  list_documents() / load_document(type) / check_document(type, text) / validate_all()
  list_samples() / load_sample(key) / list_by_type(type)
  render_outline(type) / render_check(result) / render_sample(sample)
  load_laws() / look_up(key) / unknown_articles(text)
"""

from __future__ import annotations

from .documents import (
    check_document,
    list_documents,
    load_document,
    validate_all,
)
from .laws import (
    cn_to_int,
    format_law,
    int_to_cn,
    known_articles,
    load_laws,
    look_up,
    meta,
    unknown_articles,
    verify_references,
)
from .report import format_check, render_check, render_outline, render_sample
from .samples import list_by_type, list_samples, load_sample

__version__ = "0.1.0"

__all__ = [
    "check_document",
    "cn_to_int",
    "format_check",
    "format_law",
    "int_to_cn",
    "known_articles",
    "list_by_type",
    "list_documents",
    "list_samples",
    "load_document",
    "load_laws",
    "load_sample",
    "look_up",
    "meta",
    "render_check",
    "render_outline",
    "render_sample",
    "unknown_articles",
    "validate_all",
    "verify_references",
    "__version__",
]
