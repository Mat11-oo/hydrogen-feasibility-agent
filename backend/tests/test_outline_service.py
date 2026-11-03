"""大纲解析与校验的单测（纯函数，不调模型）。"""
import pytest

from app.services.outline_service import OutlineValidationError, parse_outline


def _payload(words):
    return {
        "full_outline": [
            {"chapter_id": 7, "title": "第一章", "key_points": ["a"], "data_needed": ["总投资"], "suggested_words": words[0]},
            {"chapter_id": 2, "title": "第二章", "key_points": ["b"], "data_needed": [], "suggested_words": words[1]},
        ]
    }


def test_parse_outline_renumbers_chapters():
    chapters = parse_outline(_payload([600, 400]), target_words=1000)
    assert [c["chapter_id"] for c in chapters] == [1, 2]


def test_parse_outline_normalizes_words():
    chapters = parse_outline(_payload([300, 300]), target_words=1000)
    assert sum(c["suggested_words"] for c in chapters) == 1000


def test_parse_outline_keeps_words_when_equal():
    chapters = parse_outline(_payload([600, 400]), target_words=1000)
    assert sum(c["suggested_words"] for c in chapters) == 1000


def test_parse_outline_empty_raises():
    with pytest.raises(OutlineValidationError):
        parse_outline({"full_outline": []}, target_words=1000)
    with pytest.raises(OutlineValidationError):
        parse_outline({}, target_words=1000)


@pytest.mark.parametrize("payload", [
    [],
    {"full_outline": [None]},
    {"full_outline": [{"title": " ", "suggested_words": 100}]},
    {"full_outline": [{"title": "x", "key_points": None, "suggested_words": 100}]},
    {"full_outline": [{"title": "x", "key_points": "abc", "suggested_words": 100}]},
    {"full_outline": [{"title": "x", "suggested_words": -1}]},
    {"full_outline": [{"title": "x", "suggested_words": "bad"}]},
])
def test_invalid_model_fields_use_controlled_error(payload):
    with pytest.raises(OutlineValidationError):
        parse_outline(payload, 12000)


def test_word_rounding_preserves_target_with_zero_first_chapter():
    payload = {"full_outline": [
        {"title": f"章{i}", "suggested_words": words}
        for i, words in enumerate([0, 1, 1, 1, 1, 1])
    ]}
    chapters = parse_outline(payload, 3)
    assert sum(ch["suggested_words"] for ch in chapters) == 3
    assert all(ch["suggested_words"] >= 0 for ch in chapters)
