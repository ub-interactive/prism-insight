from prism.core.report_generation import LANGUAGE_NAMES, get_disclaimer


def test_language_names_include_chinese_and_korean():
    assert LANGUAGE_NAMES["zh"] == "Chinese"
    assert LANGUAGE_NAMES["ko"] == "Korean"


def test_get_disclaimer_chinese():
    disclaimer = get_disclaimer("zh")
    assert "投资风险提示" in disclaimer
    assert "不构成投资建议" in disclaimer


def test_get_disclaimer_english_default():
    disclaimer = get_disclaimer("en")
    assert "Investment Disclaimer" in disclaimer
