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

# Logger setup
logger = logging.getLogger(__name__)

# Prepended to Claude agent instructions: user-visible replies stay English for this codebase.
_TELEGRAM_REPLY_EN_DIRECTIVE = """## Output language (mandatory)
Compose the final user-visible reply in clear professional English. Do not use Markdown fences or headings
in the reply; use plain conversational Telegram text with emoji only when it helps readability.

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

# Constant definitions
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)  # Create directory if it doesn't exist
HTML_REPORTS_DIR = Path("html_reports")
HTML_REPORTS_DIR.mkdir(exist_ok=True)  # HTML reports directory
PDF_REPORTS_DIR = Path("pdf_reports")
PDF_REPORTS_DIR.mkdir(exist_ok=True)  # PDF reports directory

# US stock reports directory
US_REPORTS_DIR = Path("reports")
US_REPORTS_DIR.mkdir(exist_ok=True, parents=True)
US_PDF_REPORTS_DIR = Path("pdf_reports")
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
    from pdf_converter import markdown_to_pdf

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
        project_root = os.path.dirname(os.path.abspath(__file__))
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
os.chdir(project_root)

from cores.analysis import analyze_us_stock
from check_market_day import get_reference_date

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
    from pdf_converter import markdown_to_pdf

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


def generate_report_response_sync(stock_code: str, company_name: str) -> str:
    """
    Generate a KR market detailed report synchronously (legacy callers / background threads).
    """
    # Persist subprocess logs beside the orchestrator logs for RCA.
    log_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "logs" / "subprocess"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"report_{stock_code}_{timestamp}.log"

    try:
        logger.info(f"Legacy sync report subprocess starting: {stock_code} ({company_name})")
        logger.info(f"Subprocess transcript: {log_file}")

        # Reference date anchors analyze_stock payloads
        reference_date = datetime.now().strftime("%Y%m%d")

        # Spawn disposable interpreter subprocess to dodge event-loop clashes.
        cmd = [
            sys.executable,  # current Python interpreter
            "-c",
            f"""
import asyncio
import json
import sys
import logging
from datetime import datetime

# Child-process logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
subprocess_logger = logging.getLogger("subprocess_report")
subprocess_logger.info("Subprocess boot: {stock_code} ({company_name})")

from cores.analysis import analyze_stock

async def run():
    try:
        subprocess_logger.info("calling analyze_stock()")
        result = await analyze_stock(
            company_code="{stock_code}",
            company_name="{company_name}",
            reference_date="{reference_date}"
        )
        subprocess_logger.info(f"analyze_stock finished chars={{len(result) if result else 0}}")
        print("RESULT_START")
        print(json.dumps({{"success": True, "result": result}}))
        print("RESULT_END")
    except Exception as e:
        subprocess_logger.error(f"analyze_stock crashed: {{str(e)}}", exc_info=True)
        print("RESULT_START")
        print(json.dumps({{"success": False, "error": str(e)}}))
        print("RESULT_END")

if __name__ == "__main__":
    asyncio.run(run())
            """
        ]

        # Set project root directory (required for cores module import)
        project_root = os.path.dirname(os.path.abspath(__file__))

        logger.info(f"External process execution: {stock_code} (cwd: {project_root})")

        # Run with Popen to save real-time logs
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== Subprocess Log for {stock_code} ({company_name}) ===\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n")
            f.write(f"Timeout: 1800 seconds (30 min)\n")
            f.write("=" * 60 + "\n\n")
            f.flush()

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root
            )

            try:
                stdout, stderr = process.communicate(timeout=1800)  # 30 min timeout

                # Write to log file
                f.write("\n=== STDOUT ===\n")
                f.write(stdout or "(empty)")
                f.write("\n\n=== STDERR ===\n")
                f.write(stderr or "(empty)")
                f.write(f"\n\n=== Completed at: {datetime.now().isoformat()} ===\n")

            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()

                # Save log even on timeout
                f.write("\n=== TIMEOUT OCCURRED ===\n")
                f.write(f"Timeout at: {datetime.now().isoformat()}\n")
                f.write("\n=== STDOUT (before timeout) ===\n")
                f.write(stdout or "(empty)")
                f.write("\n\n=== STDERR (before timeout) ===\n")
                f.write(stderr or "(empty)")

                logger.error(f"External process timeout: {stock_code}, log file: {log_file}")
                return f"Analysis time exceeded. Check log file: {log_file}"

        # Log stderr (for debugging)
        if stderr:
            logger.warning(f"External process stderr (full log: {log_file}): {stderr[:500]}")

        # Parse output - extract only actual JSON output using delimiters
        try:
            # Extract only JSON data between RESULT_START and RESULT_END from log output
            if "RESULT_START" in stdout and "RESULT_END" in stdout:
                result_start = stdout.find("RESULT_START") + len("RESULT_START")
                result_end = stdout.find("RESULT_END")
                json_str = stdout[result_start:result_end].strip()

                # Parse JSON
                parsed_output = json.loads(json_str)

                if parsed_output.get('success', False):
                    result = parsed_output.get('result', '')
                    logger.info(f"External process result: {len(result)} characters")
                    return result
                else:
                    error = parsed_output.get('error', 'Unknown error')
                    logger.error(f"External process error: {error}, log file: {log_file}")
                    return f"Error occurred during analysis: {error}"
            else:
                # If delimiters not found - process execution itself may have issues
                logger.error(f"Could not find result delimiters in external process output. Log file: {log_file}")
                logger.error(f"stdout excerpt: {stdout[:500] if stdout else '(empty)'}")
                if stderr:
                    logger.error(f"stderr excerpt: {stderr[:500]}")
                return f"Could not find analysis result. Log file: {log_file}"
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse external process output: {e}, log file: {log_file}")
            logger.error(f"Output content: {stdout[:1000] if stdout else '(empty)'}")
            return f"Error occurred while parsing analysis result. Log file: {log_file}"
    except Exception as e:
        logger.error(f"sync report generation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Report generation failed: {str(e)}"

def clean_model_response(response):
    """Strip known tool chatter while keeping the conversational answer intact."""
    lines = response.split("\n")
    cleaned_lines = [line for line in lines if "[Calling tool" not in line]
    return "\n".join(cleaned_lines).lstrip()

async def generate_follow_up_response(ticker, ticker_name, conversation_context, user_question, tone):
    """
    Generate an AI reply for follow-up chat in an equities evaluation thread (agent pattern).

    Uses the shared global MCPApp to avoid spawning duplicate processes.

    Args:
        ticker (str): Symbol / listing code.
        ticker_name (str): Issuer label.
        conversation_context (str): Prior transcript context.
        user_question (str): Latest user message.
        tone (str): Requested conversational tone.

    Returns:
        str: Model reply ready for Telegram.
    """
    try:
        app = await get_or_create_global_mcp_app()
        app_logger = app.logger

        current_date = datetime.now().strftime('%Y%m%d')

        agent = Agent(
            name="followup_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You answer additional questions that extend an equities evaluation thread delivered over Telegram.

## Reference metadata
- Today's date (YYYYMMDD): {current_date}
- Instrument code: {ticker}
- Company / label: {ticker_name}
- Requested tone/style: {tone}

## Prior conversation (context)
{conversation_context}

## Latest user question
{user_question}

## Behaviour
1. Stay consistent with facts you already disclosed earlier in the thread.
2. Use tools only when fresh data is needed:
   - OHLC snapshots, flow prints, perplexity summaries—follow whatever MCP tooling is wired to this profile.
3. Mirror the stylistic vibe implied by "{tone}".
4. Write like a natural Telegram DM: short paragraphs, expressive emoji when it fits the tone.
5. Never format the answer as Markdown.
6. Stay under roughly 2000 characters unless the user explicitly requests more depth.
7. Honour the conversational thread—do not ignore prior commitments.

## Guardrails
- Do not narrate tool internals or "[Calling tool …]" text to the user.
- If new data is required, call tools quietly and fold only the conclusions into the reply.
""",
            server_names=["perplexity", "yahoo_finance"]
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        response = await llm.generate_str(
            message="""Draft the follow-up reply now.
Prioritize answering the user's latest question while staying coherent with earlier context.
Call tools whenever up-to-date market evidence is missing.""",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=2000
            )
        )
        app_logger.info(f"Follow-up draft preview: {str(response)[:100]}...")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"Follow-up handler error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Attempt isolated MCP restart after catastrophic failures.
        try:
            logger.warning("Triggering MCPApp reset after handler error")
            await reset_global_mcp_app()
        except Exception as reset_error:
            logger.error(f"MCPApp reset failure: {reset_error}")
        
        return "Sorry, we couldn't finish that reply. Please try again."


async def generate_evaluation_response(ticker, ticker_name, avg_price, period, tone, background, report_path=None, memory_context: str = ""):
    """
    Produce the conversational holdings-evaluation reply (agent pattern).

    Uses the shared global MCPApp to avoid spawning duplicate processes.

    Args:
        ticker (str): Symbol / listing code.
        ticker_name (str): Issuer label.
        avg_price (float): User-supplied average cost basis (currency clarified in-thread when ambiguous).
        period (int): Months held (user-supplied).
        tone (str): Desired feedback style / voice.
        background (str): Optional trade-context narrative from the user.
        report_path (str, optional): Local markdown dossier path if cached.
        memory_context (str, optional): Persisted diary / persona fragments.

    Returns:
        str: Model reply ready for Telegram.
    """
    try:
        app = await get_or_create_global_mcp_app()
        app_logger = app.logger

        current_date = datetime.now().strftime('%Y%m%d')

        background_text = f"\n- User trade context / background narrative: {background}" if background else ""

        memory_section = ""
        if memory_context:
            memory_section = f"""

                        ## User diary / memory archive (reference only)
                        The snippet below captures this user's prior journal & evaluation notes.
                        Treat it as soft context—do not overfit if it contradicts fresh data:

                        {memory_context}
                        """

        agent = Agent(
            name="evaluation_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You evaluate retail equity positions inside Prism's conversational bot.

## Position metadata
- Snapshot date (YYYYMMDD): {current_date}
- Symbol / code: {ticker}
- Display name: {ticker_name}
- User-reported average entry: {avg_price} (state the inferred currency once; if ambiguous, ask succinctly in the reply body)
- Months held (user supplied): {period}
- Tone brief: {tone}{background_text}

## Data collection outline
1. Call time-get_current_time and trust that clock for all timestamped asks.
2. Call get_stock_ohlcv spanning ~3 calendar months through today's session; never invert from/to windows.
   - Compare last close versus recent swing structure, flag volume anomalies, recompute P/L%.
   - If average entry is blank or absurd, say you need clarification in the final conversational answer.
3. Call get_stock_trading_volume across the matching window—comment on institution / foreign / retail deltas when surfaced.
4. Fire a single perplexity_ask consolidating news, filings-lite catalysts, and sector context for "{ticker} {ticker_name}" anchored to today's date/year.
5. Layer other MCP tools only if they add materially new signal; reconcile conflicts before drafting.

## Tone + overlays (honour "{tone}")
Map the user's style cues across formality, bluntness, humour, jargon density, neutral vs spicy takes. Layer overlays for winners vs losers and short-vs-long horizons just like an experienced desk teammate would.

## Formatting cues
Paragraph-first Telegram prose, emoji only when reinforcing tone, hashtags optional, no Markdown fences or headings,
<=5000 characters, never expose raw tool chatter.

## Compliance
Investment guidance stays educational—not personalized solicitation. Mention missing data plainly—do not hallucinate disclosures.
{memory_section}
""",
            server_names=["perplexity", "yahoo_finance", "time"]
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        report_content = ""
        if report_path and os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report_content = f.read()

        response = await llm.generate_str(
            message=f"""Produce the conversational evaluation reply now.

## Attachments / cached research
{report_content if report_content else "No local markdown dossier detected—lean entirely on authenticated tool pulls + perplexity synthesis."}

Follow your system brief: run tools whenever fresh data is missing, then reply in clear conversational English tuned to the user's tone.""",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=8000
            )
        )
        app_logger.info(f"evaluation_agent raw response chars={len(response)}")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"Evaluation reply failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        try:
            logger.warning("Attempting MCPApp restart after evaluation failure")
            await reset_global_mcp_app()
        except Exception as reset_error:
            logger.error(f"MCPApp restart failure: {reset_error}")
        
        return "Sorry, evaluation hit an error. Please try again."


# =============================================================================
# US equity evaluation reply helpers
# =============================================================================

async def generate_us_evaluation_response(ticker, ticker_name, avg_price, period, tone, background, memory_context: str = ""):
    """
    Generate the conversational US-listed holdings evaluation reply (agent pattern).

    Uses the shared global MCPApp to avoid spawning duplicate processes.

    Args:
        ticker (str): Ticker symbol (e.g., AAPL, MSFT).
        ticker_name (str): Issuer legal name when known (e.g., Apple Inc.).
        avg_price (float): Average cost basis expressed in USD.
        period (int): Months held (user-supplied).
        tone (str): Desired feedback style / voice.
        background (str): Trade-context narrative supplied by the user.
        memory_context (str, optional): Persisted diary / persona fragments.

    Returns:
        str: Model reply ready for Telegram (USD-labelled prices).
    """
    try:
        app = await get_or_create_global_mcp_app()
        app_logger = app.logger

        current_date = datetime.now().strftime('%Y%m%d')

        memory_section = ""
        if memory_context:
            memory_section = f"""

                        ## User diary / memory archive (reference only)
                        The snippet below captures this user's prior journal & evaluation notes.
                        Treat it as soft context—do not overfit if it contradicts fresh data:

                        {memory_context}
                        """

        background_text = f"\n- User trade context / background narrative: {background}" if background else ""

        agent = Agent(
            name="us_evaluation_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You evaluate US-listed retail equity holdings (USD cost basis) inside Prism's conversational bot.

## Position metadata
- Snapshot date (YYYYMMDD): {current_date}
- Ticker: {ticker}
- Company: {ticker_name}
- User-reported average entry: ${avg_price:,.2f} USD
- Months held (user supplied): {period}
- Tone brief: {tone}{background_text}

## Data collection outline
1. Run time-get_current_time for factual calendar grounding.
2. yahoo_finance get_historical_stock_prices ticker="{ticker}", period="3mo", interval="1d" — study last prints, swings, volume anomalies, and unrealized P/L. Recheck maths if percentages look nonsense.
3. yahoo_finance get_holder_info ticker="{ticker}", holder_type="institutional_holders" when it adds incremental signal.
4. yahoo_finance get_recommendations ticker="{ticker}" for contextual sell-side aggregates.
5. perplexity_ask (single fused query preferred) covering fresh US-listed news, filings-adjacent catalysts, macro crosswinds anchored to today's date/year.
6. Spawn extra tools only if they deliver net-new evidence; reconcile conflicts before drafting.

## Tone overlays
Honor "{tone}" like a teammate: mirror the same tonal calibration playbook used elsewhere in Prism's equity-evaluation chats—just keep every cash tag in USD.

## Formatting
Emoji ok when it reinforces tone; no Markdown; mobile-friendly pacing; hashtags optional.
<=5000 characters; never expose tool traces; ALWAYS quote actionable prices using US dollars ($).

## Compliance
Investment guidance stays educational—not personalized solicitation. Mention missing datapoints plainly.
{memory_section}
""",
            server_names=["perplexity", "yahoo_finance", "time"]
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        response = await llm.generate_str(
            message=f"""Generate the US holdings evaluation reply for {ticker_name} ({ticker}) now.
Honor the Yahoo + Perplexity workflow first if any datapoint is missing, then reply in conversational English while labelling USD figures explicitly.""",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=8000
            )
        )
        app_logger.info(f"us_evaluation_agent raw chars={len(response)}")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"US evaluation reply failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        try:
            logger.warning("Attempting MCPApp restart after US evaluation failure")
            await reset_global_mcp_app()
        except Exception as reset_error:
            logger.error(f"MCPApp restart failure: {reset_error}")

        return "Sorry, the US holdings review failed. Try again shortly."


async def generate_us_follow_up_response(ticker, ticker_name, conversation_context, user_question, tone):
    """
    Generate AI reply for US equity follow-ups (agent pattern).

    Uses the shared global MCPApp to avoid spawning duplicate processes.

    Args:
        ticker (str): Symbol (e.g., AAPL).
        ticker_name (str): Issuer label.
        conversation_context (str): Earlier chat context.
        user_question (str): Latest prompt from the trader.
        tone (str): Requested conversational tone.

    Returns:
        str: Model reply (USD-labelled prices).
    """
    try:
        app = await get_or_create_global_mcp_app()
        app_logger = app.logger

        current_date = datetime.now().strftime('%Y%m%d')

        agent = Agent(
            name="us_followup_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You answer follow-up questions about a US stock evaluation thread on Telegram.

## Reference metadata
- Today's date (YYYYMMDD): {current_date}
- Ticker: {ticker}
- Company: {ticker_name}
- Requested tone/style: {tone}

## Prior conversation
{conversation_context}

## Latest user question
{user_question}

## Behaviour
1. Stay consistent with earlier answers in the thread.
2. Tools when needed: yahoo_finance (get_historical_stock_prices, get_stock_info, get_recommendations) and perplexity_ask.
3. Mirror "{tone}" affect.
4. Telegram-friendly plain text (no Markdown), emoji ok, roughly <=2000 characters.
5. Always quote prices in USD ($).

## Guardrails
Hide tool traces; fetch live data only when necessary.
""",
            server_names=["perplexity", "yahoo_finance"]
        )

        # Connect to LLM
        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        # Generate response
        response = await llm.generate_str(
            message="""Answer the follow-up now. Prioritize the new question while honoring prior context.
Use yahoo_finance when fresh prices or fundamentals would change the narrative.""",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=2000
            )
        )
        app_logger.info(f"US follow-up response generated: {str(response)[:100]}...")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"Error generating US follow-up response: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # Try restarting global app on error
        try:
            logger.warning("Attempting to restart global MCPApp due to error")
            await reset_global_mcp_app()
        except Exception as reset_error:
            logger.error(f"MCPApp restart failure: {reset_error}")

        return "Sorry, the US follow-up response failed. Please retry."


async def generate_journal_conversation_response(
    user_id: int,
    user_message: str,
    memory_context: str,
    ticker: str = None,
    ticker_name: str = None,
    conversation_history: list = None
) -> str:
    """
    Generate an AI companion reply for journaling / reflective chat sessions.

    Args:
        user_id: Stable Telegram / account identifier.
        user_message: Latest user utterance.
        memory_context: Serialized journal snippets + evaluation breadcrumbs.
        ticker: Related symbol when the user narrowed focus (optional).
        ticker_name: Issuer-friendly label paired with ticker (optional).
        conversation_history: Short rolling transcript window (optional).

    Returns:
        str: Telegram-ready plain-text response.
    """
    try:
        # Use global MCPApp
        app = await get_or_create_global_mcp_app()
        app_logger = app.logger

        # Current date
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Ticker context
        ticker_context = ""
        if ticker and ticker_name:
            ticker_context = f"\nFocused ticker (when relevant): {ticker_name} ({ticker})"

        # Conversation history
        history_text = ""
        if conversation_history:
            history_items = []
            for item in conversation_history[-5:]:  # Last 5 items only
                role = "USER" if item.get('role') == 'user' else "ASSISTANT"
                content = item.get('content', '')[:200]
                history_items.append(f"[{role}] {content}")
            if history_items:
                history_text = "\n\n## Recent chat snippets\n" + "\n".join(history_items)

        # Create agent
        agent = Agent(
            name="journal_conversation_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You are the user's long-term investing confidant chatting over Telegram journal sessions.

## Reference date
{current_date}
{ticker_context}

## Persisted journaling / persona memory blob
{memory_context if memory_context else "(No stored journal excerpts yet — lean on conversational empathy.)"}
{history_text}

## Persona pillars
1. Speak like an experienced investing friend who remembers their journey.
2. Reference prior journal snippets only when useful—never lecture.
3. Keep tone warm even when correcting misconceptions.
4. Offer market help only when the user steers there.

## Toolkit (only if truly needed)
- perplexity_ask for fresh narratives
- yahoo_finance for US prices / fundamentals
Never overshare tool mechanics.

## Response recipe
Natural conversational English, sparing emoji when it reinforces mood, strictly NO Markdown fences, prefer roughly <=2000 characters.

## Opinion hygiene
Clearly label discretionary thoughts as personal perspective—not licensed advice.

## Boundaries
- Do not pivot every small talk ping into stocks unless invited.
- If they ask meta questions like 'what do you know about me', ground answers ONLY in persisted memory blobs—do not fantasize traits.
""",
            server_names=["perplexity", "yahoo_finance"]
        )

        # Connect to LLM
        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        # Generate response
        response = await llm.generate_str(
            message=f"""Latest user utterance:

{user_message}

Reply conversationally—personalise using stored journal motifs when grounded.""",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=2000
            )
        )
        app_logger.info(f"Journal conversation response generated: user_id={user_id}, response_len={len(response)}")

        return clean_model_response(response)

    except Exception as e:
        logger.error(f"Error generating journal conversation response: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # Try restarting global app on error
        try:
            await reset_global_mcp_app()
        except Exception:
            pass

        return "Something went wrong while drafting that reply. Mind trying again?"


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
        from firecrawl_client import firecrawl_search

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
                f"{_TELEGRAM_REPLY_EN_DIRECTIVE}"
                "Synthesize crawl snippets into investor-grade Telegram bullets.\n"
                "Prefer sourced statements; cite uncertainty plainly when evidence is thin.\n"
                "Avoid Markdown fences; plaintext + tasteful emoji only.\n"
                "Never fabricate beyond supplied URLs/snippets."
            ),
            server_names=[]
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)

        response = await llm.generate_str(
            message=f"Web corpus for synthesis:\n\n{context}\n\n---\n\nAnalyst briefing request:\n{analysis_prompt}",
            request_params=RequestParams(
                model="claude-sonnet-4-6",
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


# MCP server config per Firecrawl command type
_FIRECRAWL_CMD_SERVERS = {
    "signal": ["perplexity", "yahoo_finance"],
    "us_signal": ["perplexity", "yahoo_finance"],
    "theme": ["perplexity", "yahoo_finance"],
    "us_theme": ["perplexity", "yahoo_finance"],
    "ask": ["perplexity", "yahoo_finance"],
}

_FIRECRAWL_CMD_PERSONA = {
    "signal": "specialist dissecting catalyst impact on US equities",
    "us_signal": "specialist dissecting catalyst impact on US equities",
    "theme": "specialist diagnosing US thematic/sector breadth",
    "us_theme": "specialist diagnosing US thematic/sector breadth",
    "ask": "investment researcher focused on US-listed names",
}


async def generate_firecrawl_followup_response(
    command: str,
    query: str,
    conversation_context: str,
    user_question: str,
) -> Optional[str]:
    """
    Follow-up conversation for Firecrawl-based commands (signal, us_signal, theme, us_theme, ask).
    First response comes from Firecrawl; subsequent replies use Anthropic Sonnet 4.6
    with command-specific MCP servers so the conversation stays grounded in live data.

    Args:
        command: One of "signal", "us_signal", "theme", "us_theme", "ask"
        query: The original user query that kicked off the Firecrawl search
        conversation_context: Formatted prior conversation (initial response + follow-ups)
        user_question: The user's new follow-up question

    Returns:
        str: Claude-generated response, or None on error
    """
    try:
        app = await get_or_create_global_mcp_app()
        server_names = _FIRECRAWL_CMD_SERVERS.get(command, ["perplexity"])
        persona = _FIRECRAWL_CMD_PERSONA.get(command, "macro-aware investment analyst")

        _data_tool_guide = (
            "- Prefer yahoo_finance MCP tools first for tape + fundamentals snapshots.\n"
            "- Blend qualitative colour via perplexity_ask when timelines matter.\n"
        )
        agent = Agent(
            name="firecrawl_followup_agent",
            instruction=f"""{_TELEGRAM_REPLY_EN_DIRECTIVE}You role-play as an expert persona: **{persona}**.

## Seed prompt (original request)
{query}

## Dialogue memory
{conversation_context}

## Toolkit etiquette
{_data_tool_guide}

## Behaviour
1. Maintain continuity—do not reset context mid-thread.
2. Pull tools only when the user materially moves the question forward.
3. Telegram-native tone: emoji sparingly, ZERO Markdown fences.
4. Stay within roughly ~2000 characters unless the user escalates deliberately.
5. Never narrate MCP plumbing.
""",
            server_names=server_names,
        )

        llm = await agent.attach_llm(AnthropicAugmentedLLM)
        response = await llm.generate_str(
            message=user_question,
            request_params=RequestParams(
                model="claude-sonnet-4-6",
                maxTokens=2000,
            ),
        )
        app.logger.info(f"firecrawl_followup ({command}): {len(response)} chars")
        return clean_model_response(response)

    except Exception as e:
        logger.error(f"generate_firecrawl_followup_response failed ({command}): {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await reset_global_mcp_app()
        except Exception:
            pass
        return None
