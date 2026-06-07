import json
import logging
import re
from typing import Any, Dict, Optional


def clean_markdown(text: str) -> str:
    """Clean markdown text from LLM output artifacts."""

    # Remove tool call JSON patterns (e.g., {"name":"some-tool","arguments":{...}})
    text = re.sub(r'\{"name":\s*"[^"]+",\s*"arguments":\s*\{[^}]*\}\}', '', text)
    # Remove internal tokens (e.g., <|ipynb_marker|>, <|endoftext|>, etc.)
    text = re.sub(r'<\|[^|]+\|>', '', text)

    # Remove backtick code blocks
    text = re.sub(r'```[^\n]*\n(.*?)\n```', r'\1', text, flags=re.DOTALL)

    # Convert literal newline characters to actual newlines
    text = text.replace('\\n\\n', '\n\n')
    text = text.replace('\\n', '\n')

    # Remove newlines inside table rows (markdown table correction)
    lines = text.split('\n')
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('|') and not line.strip().endswith('|'):
            merged = line
            while i + 1 < len(lines) and not merged.strip().endswith('|'):
                i += 1
                merged += lines[i]
            cleaned_lines.append(merged)
        else:
            cleaned_lines.append(line)
        i += 1
    text = '\n'.join(cleaned_lines)

    valid_section_keywords = [
        'Analysis', 'Overview', 'Status', 'Strategy', 'Summary', 'Chart',
        'Technical', 'Fundamental', 'News', 'Market', 'Investment', 'Key', 'Point', 'Opinion',
        '1.', '2.', '3.', '4.', '5.', '1-1', '1-2', '2-1', '2-2', '3-1', '4-1', '5-1',
        'Executive',
    ]

    def is_valid_section_header(header_text):
        header_text = header_text.strip()
        if len(header_text) <= 50:
            for keyword in valid_section_keywords:
                if keyword in header_text:
                    return True
        if len(header_text) <= 50 and header_text and header_text[0].isdigit():
            return True
        return False

    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            heading_level = heading_match.group(1)
            header_content = heading_match.group(2)
            if is_valid_section_header(header_content):
                processed_lines.append(stripped)
            else:
                if len(heading_level) >= 2:
                    processed_lines.append(header_content)
                else:
                    processed_lines.append(stripped)
        else:
            processed_lines.append(line)
    text = '\n'.join(processed_lines)

    text = re.sub(r'([^\n])\n(#{1,4}\s)', r'\1\n\n\2', text)
    text = re.sub(r'(#{1,4}\s[^\n]+)\n([^\n#])', r'\1\n\n\2', text)

    lines = text.split('\n')
    result_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = stripped.startswith('|')
        prev_line = lines[i - 1].strip() if i > 0 else ''
        prev_is_table = prev_line.startswith('|')
        prev_is_empty = prev_line == ''

        if is_table_line and not prev_is_table and not prev_is_empty:
            result_lines.append('')

        result_lines.append(line)

    final_lines = []
    for i, line in enumerate(result_lines):
        final_lines.append(line)
        stripped = line.strip()
        is_table_line = stripped.startswith('|')
        if is_table_line and i + 1 < len(result_lines):
            next_line = result_lines[i + 1].strip()
            next_is_table = next_line.startswith('|')
            next_is_empty = next_line == ''
            if not next_is_table and not next_is_empty:
                final_lines.append('')

    return '\n'.join(final_lines)


# --- LLM JSON Response Parsing ---
# Consolidates duplicated regex + json_repair fallback chains.
# TODO: Replace with generate_structured() + Pydantic models to eliminate JSON parsing entirely.

_json_logger = logging.getLogger(__name__)


def fix_json_syntax(json_str: str) -> str:
    """Fix common JSON syntax errors from LLM output."""
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    json_str = re.sub(r'(\])\s*(\n\s*")', r'\1,\2', json_str)
    json_str = re.sub(r'(})\s*(\n\s*")', r'\1,\2', json_str)
    json_str = re.sub(r'([0-9]|")\s*(\n\s*")', r'\1,\2', json_str)
    json_str = re.sub(r',\s*,', ',', json_str)
    return json_str


def _extract_json_string(response: str) -> Optional[str]:
    """Extract JSON object string from LLM response text."""
    markdown_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response, re.DOTALL)
    if markdown_match:
        return markdown_match.group(1)

    json_match = re.search(r'(\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\})', response, re.DOTALL)
    if json_match:
        return json_match.group(1)

    clean = response.strip()
    if clean.startswith('{') and clean.endswith('}'):
        return clean

    return None


def parse_llm_json(
    response: str,
    context: str = 'LLM response',
) -> Optional[Dict[str, Any]]:
    """Parse JSON from an LLM text response with multi-stage recovery.

    Returns parsed dict, or None if all parsing attempts fail.
    """
    if not response or not response.strip():
        _json_logger.warning(f'[{context}] Empty response received')
        return None

    json_str = _extract_json_string(response)

    if json_str is None:
        _json_logger.warning(
            f'[{context}] No JSON object found in response (length: {len(response)})'
        )
        json_str = response

    try:
        fixed = fix_json_syntax(json_str)
        result = json.loads(fixed)
        _json_logger.debug(f'[{context}] JSON parsed successfully')
        return result
    except json.JSONDecodeError:
        pass

    try:
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
        cleaned = fix_json_syntax(cleaned)
        result = json.loads(cleaned)
        _json_logger.info(f'[{context}] JSON parsed after control character cleanup')
        return result
    except json.JSONDecodeError:
        pass

    try:
        aggressive = re.sub(r'```(?:json)?|```', '', response).strip()
        aggressive = re.sub(r'(\]|\})\s*(\n\s*"[^"]+"\s*:)', r'\1,\2', aggressive)
        aggressive = re.sub(r'(["\d\]\}])\s*\n\s*("[^"]+"\s*:)', r'\1,\n    \2', aggressive)
        aggressive = re.sub(r',(\s*[}\]])', r'\1', aggressive)
        aggressive = re.sub(r',\s*,+', ',', aggressive)
        result = json.loads(aggressive)
        _json_logger.info(f'[{context}] JSON parsed with aggressive cleanup')
        return result
    except json.JSONDecodeError:
        pass

    try:
        import json_repair
        repaired = json_repair.repair_json(response)
        result = json.loads(repaired)
        _json_logger.info(f'[{context}] JSON parsed via json_repair library')
        return result
    except ImportError:
        _json_logger.debug(f'[{context}] json_repair not installed, skipping')
    except Exception:
        pass

    _json_logger.error(
        f'[{context}] All JSON parsing attempts failed. '
        f'Response preview: {response[:300]}...'
    )
    return None
