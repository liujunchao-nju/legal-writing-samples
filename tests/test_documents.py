"""测试文书类型：加载、结构校验、要素校验。"""

from __future__ import annotations

import pytest

from lws.documents import (
    DocumentError,
    check_document,
    list_documents,
    load_document,
    validate_all,
)
from lws.report import render_outline

EXPECTED_TYPES = {
    "complaint",
    "defense",
    "arbitration",
    "appeal",
    "retrial",
    "defense-speech",
    "counterclaim",
    "preservation",
    "evidence-investigation",
    "legal-opinion",
    "lawyer-letter",
    "enforcement",
    "jurisdiction-objection",
    "withdrawal",
    "payment-order",
}


def test_validate_all_passes():
    names = validate_all()
    assert set(names) == EXPECTED_TYPES


def test_list_documents_sorted_and_documented():
    docs = list_documents()
    assert [d["type"] for d in docs] == sorted(d["type"] for d in docs)
    assert all(d.get("_file") for d in docs)
    assert all(d.get("legal_basis") for d in docs)


def test_load_unknown_type():
    with pytest.raises(KeyError):
        load_document("不存在的类型")


def test_every_document_has_structure_and_tips():
    for doc in list_documents():
        assert doc.get("structure"), doc["type"]
        assert doc.get("tips"), doc["type"]
        assert all(e.get("note") for e in doc["elements"]), doc["type"]


def test_check_document_missing_all():
    result = check_document("complaint", "这是一份空文书。")
    assert result["complete"] is False
    assert len(result["missing_required"]) == result["total_required"]
    assert result["coverage"] == 0.0


def test_check_document_complete():
    text = "原告 被告 诉讼请求 事实与理由 证据 此致 具状人"
    result = check_document("complaint", text)
    assert result["complete"] is True
    assert result["coverage"] == 100.0


def test_check_document_reports_optional():
    text = "申请人 被申请人 仲裁请求 事实与理由 证据 此致 签名"
    result = check_document("arbitration", text)
    assert result["complete"] is True
    assert any(e["id"] == "limitation" for e in result["missing_optional"])


def test_check_document_ignores_whitespace():
    text = "原 告\n被\t告\n诉 讼 请 求\n事实与理由\n证 据\n此致\n具状人"
    result = check_document("complaint", text)
    assert result["complete"] is True


def test_outline_contains_structure_and_elements():
    text = render_outline("appeal")
    assert "民事上诉状" in text
    assert "结构顺序" in text
    assert "要素清单" in text
    assert "上诉人签名与日期" in text
    assert "写作要点" in text


def test_invalid_document_rejected(tmp_path, monkeypatch):
    """缺少 keywords 的要素必须报错，而不是静默通过。"""
    import lws.documents as documents

    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "type: bad\nlabel: 坏样本\n"
        "elements:\n"
        "  - id: a\n    label: 没关键词\n    required: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(documents, "DOCUMENTS_DIR", tmp_path)
    with pytest.raises(DocumentError):
        documents.validate_all()


def test_check_document_with_party_returns_note():
    text = "原告 被告 诉讼请求 事实与理由 证据 此致 具状人"
    result = check_document("complaint", text, party="原告")
    assert result["party"] == "原告"
    assert result["party_note"]
    assert "诉讼请求" in result["party_note"]


def test_check_document_party_note_absent_for_unknown_party():
    text = "原告 被告 诉讼请求 事实与理由 证据 此致 具状人"
    result = check_document("complaint", text, party="不存在的立场")
    assert result["party_note"] is None


def test_outline_html_self_contained():
    from lws.report import render_outline_html

    html = render_outline_html("appeal")
    assert "<style" in html
    assert "http://" not in html
    assert "https://" not in html


def test_check_html_self_contained():
    from lws.report import render_check_html, render_outline

    result = check_document("complaint", "原告 被告 诉讼请求 事实与理由 证据 此致 具状人")
    html = render_check_html(result)
    assert "http://" not in html
    assert "https://" not in html

