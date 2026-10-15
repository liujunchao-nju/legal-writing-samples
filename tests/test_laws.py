"""测试法条库：加载、中文数字转换、条号提取。"""

from __future__ import annotations

import pytest

from lws.laws import (
    LawError,
    cited_articles,
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

SAMPLE_NUMBERS = [1, 10, 15, 27, 30, 67, 122, 124, 128, 171, 172, 210, 214, 216, 340, 375, 509, 563, 577, 585]


def test_laws_load_and_unique():
    index = load_laws()
    assert len(index) >= 20
    assert len(index) == len(set(index))


def test_laws_required_fields():
    for key, record in load_laws().items():
        assert record["law"], key
        assert isinstance(record["article"], int), key
        assert record["title"], key
        assert record["text"], key
        assert record["effective_from"], key


def test_meta_matches_index():
    info = meta()
    assert info["count"] == len(load_laws())
    assert info["verified_on"]
    assert info["verified_by"]


@pytest.mark.parametrize("value", SAMPLE_NUMBERS)
def test_cn_number_roundtrip(value):
    assert cn_to_int(int_to_cn(value)) == value


def test_cn_to_int_known_cases():
    assert cn_to_int("二十七") == 27
    assert cn_to_int("一百二十二") == 122
    assert cn_to_int("五百七十七") == 577


def test_int_to_cn_known_cases():
    assert int_to_cn(27) == "二十七"
    assert int_to_cn(122) == "一百二十二"
    assert int_to_cn(577) == "五百七十七"
    assert int_to_cn(509) == "五百零九"


def test_cited_articles_requires_law_name():
    assert cited_articles("依照《中华人民共和国民法典》第五百七十七条") == {577}
    assert cited_articles("《中华人民共和国民事诉讼法》第一百二十二条、第一百二十四条") == {122, 124}


def test_contract_clause_not_treated_as_law():
    """合同条款的「第×条」不应被当作法条引用。"""
    assert cited_articles("《青岛市商品房预售合同》第三十条、第三十二条") == set()
    assert cited_articles("《艺人独家合作协议》第五条") == set()


def test_unknown_articles():
    assert unknown_articles("《中华人民共和国民法典》第五百七十七条") == []
    assert unknown_articles("《中华人民共和国民法典》第九百九十九条") == [999]


def test_known_articles_cover_key_provisions():
    known = known_articles()
    assert {577, 585} <= known
    assert {122, 124, 128, 172} <= known
    assert {38, 46, 47} <= known


def test_verify_references():
    assert verify_references(["民法典第577条", "民事诉讼法第172条"]) == []
    assert verify_references(["民法典第577条", "幻想法第1条"]) == ["幻想法第1条"]


def test_look_up_miss():
    with pytest.raises(LawError):
        look_up("民事诉讼法第9999条")


def test_format_law_uses_chinese_article():
    text = format_law("民事诉讼法第172条")
    assert "第一百七十二条" in text
    assert "上诉状" in text


def test_key_article_correspondence():
    """抽查条号与内容是否对应，防止张冠李戴。"""
    index = load_laws()
    assert "上诉应当递交上诉状" in index["民事诉讼法第172条"]["text"]
    assert "十五日内" in index["民事诉讼法第171条"]["text"]
    assert "六个月" in index["民事诉讼法第216条"]["text"]
    assert "从犯" in index["刑法第27条"]["text"]
    assert "捕捞水产品" in index["刑法第340条"]["text"]
