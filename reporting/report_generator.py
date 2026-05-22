"""
Report generation and conversion module
"""
import asyncio
import atexit
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import markdown
from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from cores.config.models import get_configured_anthropic_model
from repo_paths import REPO_ROOT

# Logger setup
logger = logging.getLogger(__name__)

# Prepended to Firecrawl analyst agent: plain English, no Markdown fences.
_FIRECRAWL_ANALYST_OUTPUT_DIRECTIVE = """## Output language (mandatory)
Compose the analyst briefing in clear professional English. Do not use Markdown fences or headings in the reply;
plain text only, emoji only when it helps readability.

"""

# ============================================================================
# Global MCPApp management (prevent process accumulation)
# ============================================================================
_global_mcp_app: Optional[MCPApp] = None
_app_lock = asyncio.Lock()
_app_initialized = False


async def get_or_create_global_mcp_app() -> MCPApp:
    """
    Get or create global MCPApp instance

    Using this approach:
    - Server process starts only once
    - No new process creation per request
    - Prevents resource leaks

    Returns:
        MCPApp: Global MCPApp instance
    """
    global _global_mcp_app, _app_initialized

    async with _app_lock:
        if _global_mcp_app is None or not _app_initialized:
            logger.info("Starting global MCPApp initialization")
            _global_mcp_app = MCPApp(name="prism_report_global")
            await _global_mcp_app.initialize()
            _app_initialized = True
            logger.info(f"Global MCPApp initialization complete (Session ID: {_global_mcp_app.session_id})")
        return _global_mcp_app


async def cleanup_global_mcp_app():
    """Cleanup global MCPApp"""
    global _global_mcp_app, _app_initialized

    async with _app_lock:
        if _global_mcp_app is not None and _app_initialized:
            logger.info("Starting global MCPApp cleanup")
            try:
                await _global_mcp_app.cleanup()
                logger.info("Global MCPApp cleanup complete")
            except Exception as e:
                logger.error(f"Error during global MCPApp cleanup: {e}")
            finally:
                _global_mcp_app = None
                _app_initialized = False


async def reset_global_mcp_app():
    """Restart global MCPApp (on error)"""
    logger.warning("Attempting to restart global MCPApp")
    await cleanup_global_mcp_app()
    return await get_or_create_global_mcp_app()


def _cleanup_on_exit():
    """Cleanup on program exit"""
    global _global_mcp_app
    try:
        if _global_mcp_app is not None:
            logger.info("Cleaning up global MCPApp on program exit")
            asyncio.run(cleanup_global_mcp_app())
    except Exception as e:
        logger.error(f"Error during exit cleanup: {e}")


# Auto cleanup on program exit
atexit.register(_cleanup_on_exit)
# ============================================================================

# Constant definitions (anchored at repo root, not cwd)
REPORTS_DIR = REPO_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True, parents=True)
HTML_REPORTS_DIR = REPO_ROOT / "html_reports"
HTML_REPORTS_DIR.mkdir(exist_ok=True)
PDF_REPORTS_DIR = REPO_ROOT / "pdf_reports"
PDF_REPORTS_DIR.mkdir(exist_ok=True)

# US stock reports directory
US_REPORTS_DIR = REPO_ROOT / "reports"
US_REPORTS_DIR.mkdir(exist_ok=True, parents=True)
US_PDF_REPORTS_DIR = REPO_ROOT / "pdf_reports"
US_PDF_REPORTS_DIR.mkdir(exist_ok=True, parents=True)


# =============================================================================
# US Stock Report Caching Functions
# =============================================================================

def get_cached_us_report(ticker: str) -> tuple:
    """Search for cached US stock report

    Args:
        ticker: Ticker symbol (e.g., AAPL, MSFT)

    Returns:
        tuple: (is_cached, content, md_path, pdf_path)
    """
    # Find all report files starting with the ticker
    report_files = list(US_REPORTS_DIR.glob(f"{ticker}_*.md"))

    if not report_files:
        return False, "", None, None

    # Sort by latest
    latest_file = max(report_files, key=lambda p: p.stat().st_mtime)

    # Check if file was created within 24 hours
    file_age = datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
    if file_age.days >= 1:  # Don't use files older than 24 hours as cache
        return False, "", None, None

    # Check if corresponding PDF file exists
    pdf_file = None
    pdf_files = list(US_PDF_REPORTS_DIR.glob(f"{ticker}_*.pdf"))
    if pdf_files:
        pdf_file = max(pdf_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Generate PDF if it doesn't exist
    if not pdf_file:
        # Extract company name (filename format: {ticker}_{name}_{date}_analysis.md)
        parts = os.path.basename(latest_file).split('_')
        company_name = parts[1] if len(parts) > 1 else ticker
        pdf_file = save_us_pdf_report(ticker, company_name, latest_file)

    return True, content, latest_file, pdf_file


def save_us_report(ticker: str, company_name: str, content: str) -> Path:
    """Save US stock report to file

    Args:
        ticker: Ticker symbol (e.g., AAPL)
        company_name: Company name
        content: Report content

    Returns:
        Path: Path to saved file
    """
    reference_date = datetime.now().strftime("%Y%m%d")
    # Remove spaces and special characters from filename
    safe_company_name = company_name.replace(" ", "_").replace(".", "").replace(",", "")
    filename = f"{ticker}_{safe_company_name}_{reference_date}_analysis.md"
    filepath = US_REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"US markdown report saved: {filepath}")
    return filepath


def save_us_pdf_report(ticker: str, company_name: str, md_path: Path) -> Path:
    """Convert US stock markdown file to PDF and save

    Args:
        ticker: Ticker symbol
        company_name: Company name
        md_path: Markdown file path

    Returns:
        Path: Generated PDF file path
    """
    from reporting.pdf_converter import markdown_to_pdf

    reference_date = datetime.now().strftime("%Y%m%d")
    # Remove spaces and special characters from filename
    safe_company_name = company_name.replace(" ", "_").replace(".", "").replace(",", "")
    pdf_filename = f"{ticker}_{safe_company_name}_{reference_date}_analysis.pdf"
    pdf_path = US_PDF_REPORTS_DIR / pdf_filename

    try:
        markdown_to_pdf(str(md_path), str(pdf_path), 'playwright', add_theme=True)
        logger.info(f"US PDF report generated: {pdf_path}")
    except Exception as e:
        logger.error(f"Error converting US PDF: {e}")
        raise

    return pdf_path


def generate_us_report_response_sync(ticker: str, company_name: str) -> str:
    """
    Generate US stock detailed report synchronously (called from background thread)

    Args:
        ticker: Ticker symbol (e.g., AAPL)
        company_name: Company name (e.g., Apple Inc.)

    Returns:
        str: Generated report content
    """
    try:
        logger.info(f"US sync report generation started: {ticker} ({company_name})")

        # Set project root directory (absolute path)
        project_root = str(REPO_ROOT)
        # Run US analysis in separate process
        cmd = [
            sys.executable,  # current Python interpreter
            "-c",
            f"""
import asyncio
import json
import sys
import os

# Use absolute paths (Docker compatibility)
project_root = r'{project_root}'
sys.path.insert(0, project_root)
os.chdir(project_root)

from cores.analysis import analyze_us_stock
from cores.market_calendar import get_reference_date

async def run():
    try:
        # Auto-detect last trading day
        ref_date = get_reference_date()
        result = await analyze_us_stock(
            ticker="{ticker}",
            company_name="{company_name}",
            reference_date=ref_date,
            language="en"
        )
        # Use delimiters to mark start and end of result output
        print("RESULT_START")
        print(json.dumps({{"success": True, "result": result}}))
        print("RESULT_END")
    except Exception as e:
        # Use delimiters to mark start and end of error output
        print("RESULT_START")
        print(json.dumps({{"success": False, "error": str(e)}}))
        print("RESULT_END")

if __name__ == "__main__":
    asyncio.run(run())
            """
        ]

        logger.info(f"US external process execution: {ticker} (cwd: {project_root})")
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=1200, cwd=project_root)  # 20 min timeout

        # Log stderr (for debugging)
        if process.stderr:
            logger.warning(f"US external process stderr: {process.stderr[:500]}")

        # Initialize output - pre-declare variable to prevent warnings
        output = ""

        # Parse output - extract only actual JSON output using delimiters
        try:
            output = process.stdout
            # Extract only JSON data between RESULT_START and RESULT_END from log output
            if "RESULT_START" in output and "RESULT_END" in output:
                result_start = output.find("RESULT_START") + len("RESULT_START")
                result_end = output.find("RESULT_END")
                json_str = output[result_start:result_end].strip()

                # Parse JSON
                parsed_output = json.loads(json_str)

                if parsed_output.get('success', False):
                    result = parsed_output.get('result', '')
                    logger.info(f"US external process result: {len(result)} characters")
                    return result
                else:
                    error = parsed_output.get('error', 'Unknown error')
                    logger.error(f"US external process error: {error}")
                    return f"Error occurred during US stock analysis: {error}"
            else:
                # If delimiters not found - process execution itself may have issues
                logger.error(f"Could not find result delimiters in US external process output: {output[:500]}")
                # Check if there's error log in stderr
                if process.stderr:
                    logger.error(f"US external process error output: {process.stderr[:500]}")
                return "US analysis output could not be located. Check logs for subprocess output."
        except json.JSONDecodeError as e:
            logger.error(f"US subprocess JSON parse failure: {e}")
            logger.error(f"Stdout snippet: {output[:1000]}")
            return "Failed to parse US analysis subprocess output. See logs."

    except subprocess.TimeoutExpired:
        logger.error(f"US analysis subprocess timed out: {ticker}")
        return "US stock analysis timed out. Try again shortly."
    except Exception as e:
        logger.error(f"US sync report generation error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"US report generation error: {str(e)}"


def save_pdf_report(stock_code: str, company_name: str, md_path: Path) -> Path:
    """Convert markdown into a themed PDF artifact.

    Args:
        stock_code: Filename prefix legacy stock identifier
        company_name: Company slug for filenames (spaces become underscores downstream)
        md_path: Markdown report path on disk

    Returns:
        Path: Generated PDF destination
    """
    from reporting.pdf_converter import markdown_to_pdf

    reference_date = datetime.now().strftime("%Y%m%d")
    pdf_filename = f"{stock_code}_{company_name}_{reference_date}_analysis.pdf"
    pdf_path = PDF_REPORTS_DIR / pdf_filename

    try:
        markdown_to_pdf(str(md_path), str(pdf_path), 'playwright', add_theme=True)
        logger.info(f"PDF rendered: {pdf_path}")
    except Exception as e:
        logger.error(f"PDF rendering failed: {e}")
        raise

    return pdf_path


def get_cached_report(stock_code: str) -> tuple:
    """Return cached markdown/PDF artifact metadata when fresh enough.

    Returns:
        tuple: (is_cached, content, md_path, pdf_path).
    """
    # Find all report files starting with stock code
    report_files = list(REPORTS_DIR.glob(f"{stock_code}_*.md"))

    if not report_files:
        return False, "", None, None

    # Sort by latest
    latest_file = max(report_files, key=lambda p: p.stat().st_mtime)

    # Check if file was created within 24 hours
    file_age = datetime.now() - datetime.fromtimestamp(latest_file.stat().st_mtime)
    if file_age.days >= 1:  # Don't use files older than 24 hours as cache
        return False, "", None, None

    # Check if corresponding PDF file exists
    pdf_file = None
    pdf_files = list(PDF_REPORTS_DIR.glob(f"{stock_code}_*.pdf"))
    if pdf_files:
        pdf_file = max(pdf_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Generate PDF if it doesn't exist
    if not pdf_file:
        # Extract company name (filename format: {code}_{name}_{date}_analysis.md)
        company_name = os.path.basename(latest_file).split('_')[1]
        pdf_file = save_pdf_report(stock_code, company_name, latest_file)

    return True, content, latest_file, pdf_file


def save_report(stock_code: str, company_name: str, content: str) -> Path:
    """Persist markdown report blob to REPORTS_DIR."""
    reference_date = datetime.now().strftime("%Y%m%d")
    filename = f"{stock_code}_{company_name}_{reference_date}_analysis.md"
    filepath = REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def convert_to_html(markdown_content: str) -> str:
    """Wrap markdown → HTML boilerplate."""
    try:
        html_content = markdown.markdown(
            markdown_content,
            extensions=['markdown.extensions.fenced_code', 'markdown.extensions.tables']
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Equity research note</title>
            <style>
                body {{
                    font-family: 'Pretendard', -apple-system, system-ui, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 900px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3, h4 {{
                    color: #2563eb;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                }}
                th {{
                    background-color: #f1f5f9;
                }}
                code {{
                    background-color: #f1f5f9;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
                pre {{
                    background-color: #f1f5f9;
                    padding: 15px;
                    border-radius: 8px;
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"HTML conversion failed: {str(e)}")
        return f"<p>Unable to convert report markup: {str(e)}</p>"


def save_html_report_from_content(stock_code: str, company_name: str, html_content: str) -> Path:
    """Write HTML string to canonical html_reports folder."""
    reference_date = datetime.now().strftime("%Y%m%d")
    filename = f"{stock_code}_{company_name}_{reference_date}_analysis.html"
    filepath = HTML_REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath


def save_html_report(stock_code: str, company_name: str, markdown_content: str) -> Path:
    """Render markdown blob to themed HTML artifact."""
    html_content = convert_to_html(markdown_content)
    return save_html_report_from_content(stock_code, company_name, html_content)


def clean_model_response(response):
    """Strip known tool chatter while keeping the conversational answer intact."""
    lines = response.split("\n")
    cleaned_lines = [line for line in lines if "[Calling tool" not in line]
    return "\n".join(cleaned_lines).lstrip()

# =============================================================================
# Firecrawl Search + Claude analysis
# =============================================================================

async def generate_firecrawl_search_response(search_query: str, analysis_prompt: str, limit: int = 5) -> Optional[str]:
    """
    Cost-efficient Firecrawl /search (2 credits) + Claude Sonnet analysis.
    Uses the same global MCPApp pattern as other generate_* functions.

    Args:
        search_query: Web search query for Firecrawl
        analysis_prompt: Prompt for Claude to analyze the search results
        limit: Number of search results (default 5)

    Returns:
        str: Claude-generated analysis, or None on error
    """
    try:
        from integrations.firecrawl_client import firecrawl_search

        # Step 1: Firecrawl search with full article content
        # with_content=True fetches markdown body per result — much richer than meta descriptions.
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: firecrawl_search(search_query, limit=limit, with_content=True)
        )
        items = result.web if result and result.web else []

        if not items:
            logger.warning(f"No search results for: {search_query[:50]}, falling back to Claude-only analysis")
            context = "(No fresh web hits — proceed strictly from retrieval-safe general knowledge caveats)\n\n"
        else:
            # Step 2: Build context — prefer full markdown, fall back to description snippet
            context = ""
            for item in items:
                title = getattr(item, 'title', '') or ''
                url = getattr(item, 'url', '') or ''
                desc = getattr(item, 'description', '') or ''
                # markdown is populated when with_content=True; truncate to 2000 chars per article
                markdown = getattr(item, 'markdown', '') or ''
                body = markdown[:2000] if markdown else desc
                context += f"[{title}]\nURL: {url}\n{body}\n\n"

            logger.info(f"Search context built: {len(items)} results, {len(context)} chars")

        # Step 3: Use global MCPApp + Claude Sonnet for analysis
        app = await get_or_create_global_mcp_app()

        agent = Agent(
            name="firecrawl_search_analyst",
            instruction=(
                f"{_FIRECRAWL_ANALYST_OUTPUT_DIRECTIVE}"
                "Synthesize crawl snippets into a concise investor-facing briefing.\n"
                "Prefer sourced statements; cite uncertainty plainly when evidence is thin.\n"
                "Plaintext only with tasteful emoji when helpful.\n"
                "Never fabricate beyond supplied URLs/snippets."
            ),
            server_names=[]
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        response = await llm.generate_str(
            message=f"Web corpus for synthesis:\n\n{context}\n\n---\n\nAnalyst briefing request:\n{analysis_prompt}",
            request_params=RequestParams(
                model=get_configured_anthropic_model("firecrawl_analyst", "claude-sonnet-4-6"),
                maxTokens=2000
            )
        )
        app.logger.info(f"Firecrawl search+Claude response: {len(response)} chars")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"generate_firecrawl_search_response failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

        try:
            await reset_global_mcp_app()
        except Exception:
            pass

        return None

