"""
Report translation module
"""
import re
import logging
from typing import Dict, Tuple

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from prism.core.shared.config.models import get_configured_model

logger = logging.getLogger(__name__)


def extract_and_replace_charts(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Find all chart divs or standalone img tags and replace them with placeholder comments to save tokens and prevent corruption.
    Matches image elements containing base64 data.
    """
    charts = {}
    # Matches either <div style="text-align: center;">...</div> blocks or standalone <img ...> with base64 img inside
    pattern = r'(<div style="text-align: center;">\s*<img [^>]*src="data:image/[^>]+>\s*</div>|<img [^>]*src="data:image/[^>]+>)'

    matches = re.findall(pattern, text)
    processed_text = text
    for idx, match in enumerate(matches):
        placeholder = f"<!-- CHART_PLACEHOLDER_{idx} -->"
        charts[placeholder] = match
        processed_text = processed_text.replace(match, placeholder)

    return processed_text, charts


def restore_charts(text: str, charts: Dict[str, str]) -> str:
    """Restore placeholders back to original chart divs."""
    restored_text = text
    for placeholder, chart_html in charts.items():
        restored_text = restored_text.replace(placeholder, chart_html)
    return restored_text


async def translate_text(text: str, target_lang: str) -> str:
    """Translate a chunk of text to the target language using the configured translation model."""
    if not text.strip():
        return text

    # Load translation model configuration from YAML
    model_name = get_configured_model("us_translation", "gpt-5.4-mini")

    lang_names = {
        "zh": "Chinese",
        "ko": "Korean",
        "ja": "Japanese",
        "es": "Spanish",
        "fr": "French",
        "de": "German"
    }
    lang_name = lang_names.get(target_lang.lower(), target_lang)

    agent = Agent(
        name="report_translator",
        instruction=(
            "You are a professional financial translator. "
            "Translate all English text to the target language accurately and professionally. "
            "Preserve all markdown formatting, lists, bold text, tables, footnote markers, "
            "footnote definition labels, and HTML comments/placeholders exactly."
        ),
        server_names=[]
    )

    llm = await agent.attach_llm(OpenAIAugmentedLLM)

    prompt = (
        f"Translate the following text into standard financial terminology in {lang_name}. "
        "Preserve all markdown headers, bold text, tables, bullet points, HTML comments, and placeholders exactly as they are. "
        "Preserve markdown footnote markers like [^1] exactly. "
        "Preserve footnote definition labels like [^1]: exactly; translate only the definition text after the label. "
        "Output only the translated text, with no conversational preamble, explanation, or introduction:\n\n"
        f"{text}"
    )

    response = await llm.generate_str(
        message=prompt,
        request_params=RequestParams(
            model=model_name,
            maxTokens=4000
        )
    )

    cleaned_response = response.strip()
    # Strip any markdown codeblock backticks if the model added them
    if cleaned_response.startswith("```markdown"):
        cleaned_response = cleaned_response[11:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
    elif cleaned_response.startswith("```"):
        cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

    return cleaned_response


async def translate_report(text: str, target_lang: str) -> str:
    """
    Translate the entire markdown report into the target language.
    Splits the document by H2 headers and processes each section independently
    to avoid hitting token limits, keeping base64 images safe.
    """
    if not target_lang or target_lang.lower() == "en":
        return text

    logger.info(f"Starting translation of the report into: {target_lang}")

    # 1. Extract and replace base64 HTML charts
    processed_text, charts = extract_and_replace_charts(text)

    # 2. Split report by H2 headers (##) to translate section-by-section
    # Keep the delimiter (## ...) as part of the section content by using lookahead
    sections = re.split(r'(?=^##\s+)', processed_text, flags=re.MULTILINE)

    translated_sections = []
    for idx, section in enumerate(sections):
        if not section.strip():
            continue
        logger.info(f"Translating report segment {idx+1}/{len(sections)} ({len(section)} chars)...")
        try:
            translated_section = await translate_text(section, target_lang)
            translated_sections.append(translated_section)
        except Exception as e:
            logger.error(f"Failed to translate segment {idx+1}: {e}")
            # Fallback to original section if translation fails
            translated_sections.append(section)

    # 3. Join the sections
    translated_report = "\n\n".join(translated_sections)

    # 4. Restore base64 HTML charts
    final_report = restore_charts(translated_report, charts)

    logger.info("Report translation complete.")
    return final_report
