"""测试命令行接口。"""

from __future__ import annotations

import pathlib

from lws.cli import main

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_cli_list(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "complaint" in out
    assert "民事起诉状" in out
    assert "15 篇范文" in out


def test_cli_show_type(capsys):
    assert main(["show", "--type", "retrial"]) == 0
    out = capsys.readouterr().out
    assert "民事再审申请书" in out
    assert "民事诉讼法第210条" in out
    assert "05-retrial-house" in out


def test_cli_show_sample(capsys):
    assert main(["show", "--sample", "06"]) == 0
    out = capsys.readouterr().out
    assert "刑事辩护词" in out
    assert "指导性案例213号" in out
    assert "参照原文" in out


def test_cli_show_requires_target(capsys):
    assert main(["show"]) == 2


def test_cli_outline(capsys):
    assert main(["outline", "--type", "arbitration"]) == 0
    out = capsys.readouterr().out
    assert "写作大纲" in out
    assert "仲裁时效说明" in out


def test_cli_check_sample_passes(capsys):
    for slug in [f"{i:02d}" for i in range(1, 16)]:
        assert main(["check", "--sample", slug]) == 0, slug
    capsys.readouterr()


def test_cli_outline_party(capsys):
    assert main(["outline", "--type", "complaint", "--party", "原告"]) == 0
    out = capsys.readouterr().out
    assert "立场视角" in out
    assert "原告" in out


def test_cli_outline_html_self_contained(capsys, tmp_path):
    out_file = tmp_path / "outline.html"
    code = main(
        ["outline", "--type", "complaint", "--format", "html", "--out", str(out_file)]
    )
    assert code == 0
    html = out_file.read_text(encoding="utf-8")
    assert "<html" in html or "<!DOCTYPE" in html or "<style" in html
    assert "http://" not in html
    assert "https://" not in html


def test_cli_check_html_self_contained(capsys, tmp_path):
    out_file = tmp_path / "check.html"
    code = main(
        ["check", "--type", "complaint", "--sample", "01",
         "--format", "html", "--out", str(out_file)]
    )
    assert code == 0
    html = out_file.read_text(encoding="utf-8")
    assert "http://" not in html
    assert "https://" not in html


def test_cli_check_file_missing_elements(capsys, tmp_path):
    bad = tmp_path / "draft.md"
    bad.write_text("原告：某某\n诉讼请求：支付货款\n", encoding="utf-8")
    code = main(["check", "--type", "complaint", "--file", str(bad)])
    assert code == 1
    out = capsys.readouterr().out
    assert "缺失必备要素" in out


def test_cli_check_markdown(capsys, tmp_path):
    out_file = tmp_path / "report.md"
    code = main(
        ["check", "--type", "complaint", "--file", str(ROOT / "lws/data/samples/01-complaint-sales.md"),
         "--markdown", "--out", str(out_file)]
    )
    assert code == 0
    text = out_file.read_text(encoding="utf-8")
    assert "要素校验" in text


def test_cli_check_without_target(capsys):
    assert main(["check"]) == 2


def test_cli_laws_key(capsys):
    assert main(["laws", "--key", "刑法第27条"]) == 0
    assert "从犯" in capsys.readouterr().out


def test_cli_laws_all(capsys):
    assert main(["laws"]) == 0
    out = capsys.readouterr().out
    assert "核验于" in out
    assert "民事诉讼法第172条" in out


def test_cli_laws_unknown_key(capsys):
    assert main(["laws", "--key", "刑法第9999条"]) == 1


def test_cli_verify(capsys):
    assert main(["verify"]) == 0
    out = capsys.readouterr().out
    assert "结构校验通过" in out
    assert "范文条号全部可追溯" in out
