"""测试范文：front matter、来源标注与自检通过率。

最重要的一条是 test_every_sample_passes_its_own_check：
每篇范文都必须能通过其所属文书类型的要素校验。
新增范文若漏了必备要素，测试会立刻失败。
"""

from __future__ import annotations

import pytest

from lws.documents import check_document, list_documents
from lws.samples import (
    SampleError,
    list_by_type,
    list_samples,
    load_sample,
    validate_all,
)

EXPECTED_SLUGS = {
    "01-complaint-sales",
    "02-defense-sales",
    "03-arbitration-labor",
    "04-appeal-labor",
    "05-retrial-house",
    "06-defense-speech-fishing",
}


def test_validate_all_passes():
    slugs = validate_all()
    assert set(slugs) == EXPECTED_SLUGS


def test_load_sample_by_full_slug():
    sample = load_sample("01-complaint-sales")
    assert sample["type"] == "complaint"


def test_load_sample_by_prefix():
    assert load_sample("02")["type"] == "defense"
    assert load_sample("06")["type"] == "defense-speech"


def test_load_sample_unknown():
    with pytest.raises(KeyError):
        load_sample("99")


def test_every_sample_has_reference_metadata():
    for sample in list_samples():
        ref = sample["reference"]
        assert ref.get("case_name"), sample["_slug"]
        assert ref.get("source"), sample["_slug"]
        assert ref.get("notes"), sample["_slug"]
        assert ref.get("case_id") or "指导性案例" in ref.get("source", ""), sample["_slug"]


def test_every_sample_passes_its_own_check():
    """范文必须自洽：按所属类型的要素清单校验，应当要素齐备。"""
    for sample in list_samples():
        result = check_document(sample["type"], sample["_body"])
        assert result["complete"], f"{sample['_slug']} 缺失: {[e['label'] for e in result['missing_required']]}"


def test_every_document_type_has_sample():
    for doc in list_documents():
        assert list_by_type(doc["type"]), f"{doc['type']} 没有任何范文"


def test_samples_cover_two_sides_of_same_case():
    """01 与 02 应当参照同一案件，形成原被告对照。"""
    first = load_sample("01")
    second = load_sample("02")
    assert first["reference"]["case_id"] == second["reference"]["case_id"]


def test_samples_cover_two_stages_of_same_case():
    """03 与 04 应当参照同一案件，形成仲裁与上诉两阶段的对照。"""
    arbitration = load_sample("03")
    appeal = load_sample("04")
    assert arbitration["reference"]["case_id"] == appeal["reference"]["case_id"]


def test_sample_body_is_not_empty():
    for sample in list_samples():
        assert len(sample["_body"]) > 500, sample["_slug"]


def test_invalid_sample_rejected(tmp_path, monkeypatch):
    """缺少 reference 的范文必须报错。"""
    import lws.samples as samples

    bad = tmp_path / "bad.md"
    bad.write_text("---\ntype: complaint\ntitle: 缺来源\n---\n\n正文\n", encoding="utf-8")
    monkeypatch.setattr(samples, "SAMPLES_DIR", tmp_path)
    with pytest.raises(SampleError):
        samples.validate_all()
