"""命令行入口。

六条命令：
  list      列出文书类型与范文
  show      查看某类文书的定义，或某篇范文的全文
  outline   生成某类文书的写作大纲
  check     校验一份文书是否具备必备要素
  laws      查看经核验的法条库
  verify    校验全部数据文件的结构与引用
"""

from __future__ import annotations

import argparse
import sys

from .documents import check_document, list_documents, load_document
from .documents import validate_all as validate_documents
from .laws import load_laws, meta
from .report import (
    format_check,
    render_check,
    render_check_html,
    render_outline,
    render_outline_html,
    render_sample,
)
from .samples import list_by_type, list_samples, load_sample
from .samples import validate_all as validate_samples

__all__ = ["main"]


def _cmd_list(args) -> int:
    docs = list_documents()
    samples = list_samples()
    width = max(len(d["type"]) for d in docs)
    counts = {d["type"]: len(list_by_type(d["type"])) for d in docs}
    for doc in docs:
        cat = doc.get("category", "")
        suffix = f"　[{cat}]" if cat else ""
        print(f"{doc['type'].ljust(width)}  {doc['label']}　范文 {counts[doc['type']]} 篇{suffix}")
    print("")
    print(f"共 {len(docs)} 类文书，{len(samples)} 篇范文")
    return 0


def _cmd_show(args) -> int:
    if args.sample:
        sample = load_sample(args.sample)
        sys.stdout.write(render_sample(sample))
        return 0
    if not args.type:
        print("请用 --type 指定文书类型，或用 --sample 指定范文", file=sys.stderr)
        return 2
    doc = load_document(args.type)
    index = load_laws()
    print(f"类型: {doc['type']}")
    print(f"名称: {doc['label']}")
    print(f"分类: {doc.get('category', '')}")
    print(f"文件: {doc['_file']}")
    if doc.get("usage"):
        print(f"适用: {' '.join(str(doc['usage']).split())}")
    basis = doc.get("legal_basis") or []
    if basis:
        print("主要依据:")
        for key in basis:
            record = index.get(key)
            if record:
                print(f"  {record['law']}第{record['article']}条　{record['title']}")
            else:
                print(f"  {key}（未核验）")
    samples = list_by_type(doc["type"])
    if samples:
        print("范文:")
        for sample in samples:
            ref = sample.get("reference") or {}
            print(f"  {sample['_slug']}　{ref.get('case_id', '')}　{ref.get('case_name', '')}")
    return 0


def _cmd_outline(args) -> int:
    if args.format == "html":
        text = render_outline_html(args.type, args.party)
    else:
        text = render_outline(args.type, args.party)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"已写入 {args.out}")
    else:
        sys.stdout.write(text)
    return 0


def _cmd_check(args) -> int:
    doc_type = args.type
    if args.sample:
        sample = load_sample(args.sample)
        doc_type = doc_type or sample["type"]
        text = sample["_body"]
    elif args.file:
        with open(args.file, encoding="utf-8") as fh:
            text = fh.read()
    else:
        print("请用 --file 指定待校验文书，或用 --sample 校验范文", file=sys.stderr)
        return 2

    if not doc_type:
        print("请用 --type 指定文书类型", file=sys.stderr)
        return 2

    result = check_document(doc_type, text, args.party)
    if args.format == "html":
        out = render_check_html(result, args.party)
    elif args.markdown:
        out = render_check(result, args.party)
    else:
        print(format_check(result))
        return 0 if result["complete"] else 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out)
        print(f"已写入 {args.out}")
    else:
        sys.stdout.write(out)
    return 0 if result["complete"] else 1


def _cmd_laws(args) -> int:
    index = load_laws()
    if args.key:
        record = index.get(args.key)
        if not record:
            print(f"未找到法条: {args.key}", file=sys.stderr)
            return 1
        print(f"{record['law']}第{record['article']}条　{record['title']}")
        print(f"施行日期: {record['effective_from']}　效力层级: {record['authority']}")
        print("原文:")
        print(f"  {record['text']}")
        return 0
    info = meta()
    print(f"共 {info['count']} 条，核验于 {info['verified_on']}")
    print(f"来源: {info['verified_by']}")
    print("")
    width = max(len(k) for k in index)
    for key, record in index.items():
        print(f"{key.ljust(width)}  {record['title']}")
    return 0


def _cmd_verify(args) -> int:
    docs = validate_documents()
    slugs = validate_samples()
    info = meta()
    print(f"文书类型 {len(docs)} 类: {', '.join(docs)}")
    print(f"范文 {len(slugs)} 篇: {', '.join(slugs)}")
    print(f"法条库 {info['count']} 条，核验于 {info['verified_on']}")
    print("结构校验通过，引用全部命中法条库，范文条号全部可追溯。")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lws",
        description="法律文书范文库：要素模型、写作大纲与条号校验",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出文书类型与范文").set_defaults(func=_cmd_list)

    show = sub.add_parser("show", help="查看文书定义或范文全文")
    show.add_argument("--type", help="文书类型")
    show.add_argument("--sample", help="范文文件名或序号前缀")
    show.set_defaults(func=_cmd_show)

    outline = sub.add_parser("outline", help="生成写作大纲")
    outline.add_argument("--type", required=True)
    outline.add_argument("--party", help="立场视角，如 原告 / 被告 / 上诉人 / 被申请人 / 辩护人")
    outline.add_argument("--format", choices=["md", "html"], default="md", help="输出格式（html 为单文件离线网页）")
    outline.add_argument("--out", help="输出文件；缺省打印到终端")
    outline.set_defaults(func=_cmd_outline)

    check = sub.add_parser("check", help="校验文书要素是否齐备")
    check.add_argument("--type", help="文书类型；配合 --sample 时可省略")
    check.add_argument("--file", help="待校验的文书文本")
    check.add_argument("--sample", help="校验某篇范文自身")
    check.add_argument("--party", help="立场视角，如 原告 / 被告 / 上诉人 / 被申请人 / 辩护人")
    check.add_argument("--format", choices=["md", "html"], default="md", help="输出格式（html 为单文件离线网页）")
    check.add_argument("--markdown", action="store_true", help="输出 Markdown 报告（等价于 --format md）")
    check.add_argument("--out", help="配合 --format/--markdown 写入文件")
    check.set_defaults(func=_cmd_check)

    laws = sub.add_parser("laws", help="查看经核验的法条库")
    laws.add_argument("--key", help="查看某一条的原文")
    laws.set_defaults(func=_cmd_laws)

    sub.add_parser("verify", help="校验数据文件结构与条号引用").set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
