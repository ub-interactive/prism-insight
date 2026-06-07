from prism.core.shared.config.models import get_optional_reasoning_effort


def test_reasoning_effort_omitted_for_none():
    assert get_optional_reasoning_effort("gpt-5.4-mini", "none") == {}
    assert get_optional_reasoning_effort("gpt-5.4-mini", "") == {}


def test_reasoning_effort_omitted_for_non_openai_models():
    assert get_optional_reasoning_effort("deepseek-chat", "low") == {}


def test_reasoning_effort_included_when_supported():
    assert get_optional_reasoning_effort("gpt-5.4-mini", "low") == {
        "reasoning_effort": "low"
    }
