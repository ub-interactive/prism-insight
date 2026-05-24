#!/usr/bin/env python3
"""
US Stock Analysis Orchestrator

Overall Process:
1. Execute time-based trigger batch jobs for US equities
2. Generate markdown research dossiers plus companion PDF artifacts
3. Run the downstream tracking/trading sweep that applies portfolio rules

Key pipeline traits:
- Uses ticker symbols (AAPL, MSFT) instead of six-digit numeric codes.
- Sources market data primarily through yfinance and US-ready agents.
- Follows regular US equity session conventions (weekday NYSE/NASDAQ hours).
- Narrative summaries default to formal English (`language="en"`).
"""
from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

_repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo / "src"))
from prism.paths import LOGS_DIR, MCP_CONFIG_PATH, PDF_REPORTS_DIR, REPORTS_DIR, REPO_ROOT, TRIGGER_RESULTS_DIR

from prism.core.config.models import get_configured_model, get_optional_reasoning_effort
from prism.core.openai.error_logging import log_openai_error

# Directory configuration (before logging — FileHandler needs LOGS_DIR)
US_REPORTS_DIR = REPORTS_DIR
US_PDF_REPORTS_DIR = PDF_REPORTS_DIR
LOGS_DIR.mkdir(exist_ok=True, parents=True)
TRIGGER_RESULTS_DIR.mkdir(exist_ok=True, parents=True)
US_REPORTS_DIR.mkdir(exist_ok=True, parents=True)
US_PDF_REPORTS_DIR.mkdir(exist_ok=True, parents=True)

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / f"us_orchestrator_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)


def _import_proxy_safe():
    """Import chatgpt_proxy from canonical cores package."""
    import prism.core.chatgpt_proxy as proxy_mod
    return proxy_mod

US_MACRO_ANALYSIS_MODEL = get_configured_model("us_macro_analysis", "gpt-5.4-mini")
US_REPORT_FILENAME_MODEL = get_configured_model("us_report_filename", US_MACRO_ANALYSIS_MODEL)


def _model_slug(model_name: str) -> str:
    """Create a safe filename suffix from model name."""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", (model_name or "").strip())
    return slug.strip("-") or "model"


class USStockAnalysisOrchestrator:
    """US stock analysis pipeline orchestrator."""

    def __init__(self):
        self.selected_tickers = {}

    async def run_macro_intelligence(self, reference_date: str = None, language: str = "en") -> dict:
        """
        Run macro intelligence analysis for US market.

        Step 1: Prefetch index data (S&P 500/NASDAQ/VIX) programmatically
        Step 2: Compute market regime from actual price data (not LLM)
        Step 3: Run LLM agent with perplexity only for qualitative analysis

        Args:
            reference_date: Analysis date (YYYYMMDD). Defaults to today.
            language: Legacy language kwarg forwarded to upstream agents.

        Returns:
            dict: Macro context with regime, sectors, risks, report_prose.
                  Returns None if macro intelligence fails (graceful degradation).
        """
        if reference_date is None:
            reference_date = datetime.now().strftime("%Y%m%d")

        logger.info(f"Starting macro intelligence analysis for US market - date: {reference_date}")

        try:
            # Step 1: Prefetch index data and compute regime programmatically
            from prism.core.data.prefetch import prefetch_us_macro_intelligence_data
            prefetched = prefetch_us_macro_intelligence_data(reference_date)
            logger.info(f"US macro prefetch complete: {list(prefetched.keys())}")

            if prefetched.get("computed_regime"):
                computed = prefetched["computed_regime"]
                logger.info(f"Pre-computed US regime: {computed.get('market_regime')} "
                           f"(confidence: {computed.get('regime_confidence')})")

            # Step 2: Run LLM agent with perplexity for qualitative analysis
            from mcp_agent.app import MCPApp
            from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
            from prism.core.agents.macro_intelligence_agent import create_macro_intelligence_agent

            macro_app = MCPApp(name="us_macro_intelligence", settings=str(MCP_CONFIG_PATH))

            async with macro_app.run() as macro_run_context:
                macro_logger = macro_run_context.logger
                macro_logger.info("US macro intelligence agent starting (perplexity-only mode)...")

                agent = create_macro_intelligence_agent(reference_date, language, prefetched_data=prefetched)

                from mcp_agent.workflows.llm.augmented_llm import RequestParams
                llm = await agent.attach_llm(OpenAIAugmentedLLM)
                result = await llm.generate_str(
                    message=f"Execute US stock market macro analysis for {reference_date} and output JSON.",
                    request_params=RequestParams(
                        model=US_MACRO_ANALYSIS_MODEL,
                        maxTokens=16000,
                        parallel_tool_calls=True,
                        use_history=True,
                        **get_optional_reasoning_effort(US_MACRO_ANALYSIS_MODEL, "none"),
                    )
                )

                macro_logger.info(f"US macro intelligence raw output: {len(result)} chars")

                # Save raw output for debugging
                try:
                    raw_output_path = f"macro_intelligence_us_{reference_date}.json"
                    with open(raw_output_path, 'w', encoding='utf-8') as f:
                        f.write(result)
                    macro_logger.info(f"Raw output saved to: {raw_output_path}")
                except Exception:
                    pass

                # Parse JSON from agent output
                import json as json_module
                macro_data = None

                try:
                    macro_data = json_module.loads(result.strip())
                except json_module.JSONDecodeError:
                    import re
                    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', result, re.DOTALL)
                    if json_match:
                        try:
                            macro_data = json_module.loads(json_match.group(1).strip())
                        except json_module.JSONDecodeError:
                            pass

                    if not macro_data:
                        try:
                            from json_repair import repair_json
                            macro_data = json_module.loads(repair_json(result))
                        except Exception:
                            macro_logger.error("Failed to parse US macro intelligence output as JSON")

                # Fallback: if LLM failed but we have computed regime, use that
                if not macro_data and prefetched.get("computed_regime"):
                    macro_logger.warning("LLM output parsing failed, using computed regime only")
                    macro_data = {
                        "analysis_date": reference_date,
                        "market": "US",
                        **prefetched["computed_regime"],
                        "regime_rationale": "Programmatically computed from S&P 500 / VIX data",
                        "leading_sectors": [],
                        "lagging_sectors": [],
                        "risk_events": [],
                        "beneficiary_themes": [],
                        "report_prose": "",
                    }
                elif not macro_data:
                    return None

                regime = macro_data.get("market_regime", "sideways")
                macro_logger.info(f"US macro intelligence complete - regime: {regime}, "
                                 f"leading_sectors: {len(macro_data.get('leading_sectors', []))}, "
                                 f"risk_events: {len(macro_data.get('risk_events', []))}")

                return macro_data

        except Exception as e:
            log_openai_error(logger, e, "US macro intelligence")
            logger.error(f"US macro intelligence failed (graceful degradation): {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def run_trigger_batch(self, mode: str, macro_context: dict = None, override_date: str = None):
        """
        Execute US trigger batch and save results

        Args:
            mode: 'morning' or 'afternoon'

        Returns:
            list: List of selected stock info dictionaries
        """
        logger.info(f"Starting US trigger batch execution: {mode}")
        try:
            from prism.ops.pipelines.trigger_batch import run_batch

            # Results file path (consistent with trigger_batch naming)
            effective_date = override_date if override_date else datetime.now().strftime("%Y%m%d")
            results_file = str(TRIGGER_RESULTS_DIR / f"trigger_results_us_{mode}_{effective_date}.json")

            # Run batch
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: run_batch(mode, "INFO", results_file, macro_context=macro_context, override_date=override_date)
            )

            if not results:
                logger.warning("US batch returned empty results")
                return []

            # Read results file for full data with metadata
            if os.path.exists(results_file):
                with open(results_file, 'r', encoding='utf-8') as f:
                    full_results = json.load(f)
                self.selected_tickers[mode] = full_results

            # Extract stock info from results
            tickers = []
            ticker_set = set()

            for trigger_type, stocks_df in results.items():
                if hasattr(stocks_df, 'index'):
                    for ticker in stocks_df.index:
                        if ticker not in ticker_set:
                            ticker_set.add(ticker)

                            # Get company name
                            name = ""
                            if "CompanyName" in stocks_df.columns:
                                name = stocks_df.loc[ticker, "CompanyName"]

                            # Get risk_reward_ratio if available
                            rr_ratio = 0
                            if "risk_reward_ratio" in stocks_df.columns:
                                rr_ratio = float(stocks_df.loc[ticker, "risk_reward_ratio"])

                            tickers.append({
                                'ticker': ticker,
                                'name': name or ticker,
                                'trigger_type': trigger_type,
                                'trigger_mode': mode,
                                'risk_reward_ratio': rr_ratio
                            })

            logger.info(f"Number of selected US stocks: {len(tickers)}")
            return tickers

        except Exception as e:
            logger.error(f"Error during US trigger batch execution: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def generate_reports(self, tickers: list, mode: str, timeout: int = None, language: str = "en", macro_context: dict = None) -> list:
        """
        Generate reports serially for all US stocks.

        Args:
            tickers: List of stocks to analyze
            mode: Execution mode
            timeout: Timeout (seconds)
            language: Analysis language (default: "en")

        Returns:
            list: List of successful report paths
        """
        logger.info(f"Starting US report generation for {len(tickers)} stocks (serial processing)")

        successful_reports = []

        for idx, ticker_info in enumerate(tickers, 1):
            if isinstance(ticker_info, dict):
                ticker = ticker_info.get('ticker')
                company_name = ticker_info.get('name', ticker)
            else:
                ticker = ticker_info
                company_name = ticker

            logger.info(f"[{idx}/{len(tickers)}] Starting US stock analysis: {company_name}({ticker})")

            reference_date = datetime.now().strftime("%Y%m%d")
            output_file = str(
                US_REPORTS_DIR / f"{ticker}_{company_name}_{reference_date}_{mode}_{_model_slug(US_REPORT_FILENAME_MODEL)}.md"
            )

            try:
                from prism.core.analysis import analyze_us_stock

                logger.info(f"[{idx}/{len(tickers)}] Starting analyze_us_stock function call")
                report = await analyze_us_stock(
                    ticker=ticker,
                    company_name=company_name,
                    reference_date=reference_date,
                    language=language,
                    macro_context=macro_context
                )

                if report and len(report.strip()) > 0:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(report)
                    logger.info(f"[{idx}/{len(tickers)}] Report generation complete: {company_name}({ticker}) - {len(report)} characters")
                    successful_reports.append(output_file)
                else:
                    logger.error(f"[{idx}/{len(tickers)}] Report generation failed: {company_name}({ticker}) - empty content")

            except Exception as e:
                logger.error(f"[{idx}/{len(tickers)}] Error during analysis: {company_name}({ticker}) - {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        logger.info(f"US report generation complete: {len(successful_reports)}/{len(tickers)} successful")
        return successful_reports

    async def convert_to_pdf(self, report_paths: list) -> list:
        """
        Convert markdown reports to PDF

        Args:
            report_paths: List of markdown report file paths

        Returns:
            list: List of generated PDF file paths
        """
        logger.info(f"Starting PDF conversion for {len(report_paths)} US reports")
        pdf_paths = []

        from prism.reporting.pdf_converter import markdown_to_pdf

        for report_path in report_paths:
            try:
                report_file = Path(report_path)
                pdf_file = US_PDF_REPORTS_DIR / f"{report_file.stem}.pdf"

                # Convert markdown to PDF
                markdown_to_pdf(report_path, pdf_file, 'playwright', add_theme=True, enable_watermark=False)

                logger.info(f"PDF conversion complete: {pdf_file}")
                pdf_paths.append(pdf_file)

            except Exception as e:
                logger.error(f"Error during PDF conversion of {report_path}: {str(e)}")

        return pdf_paths

    def _create_trigger_alert_message(self, mode: str, results: dict, trade_date: str, language: str = "en") -> str:
        """
        Format a human-readable trigger scan digest from US trigger results (logging / operators).

        Args:
            mode: 'morning' or 'afternoon'
            results: Trigger results dictionary (includes 'metadata' key with hybrid selection info)
            trade_date: Trade date in YYYYMMDD format
            language: Unused legacy argument kept for callers.
        """
        _ = language
        formatted_date = f"{trade_date[:4]}.{trade_date[4:6]}.{trade_date[6:8]}"

        # Extract metadata for hybrid selection info
        metadata = results.get("metadata", {})
        market_regime = metadata.get("market_regime")
        selection_strategy = metadata.get("selection_strategy", "")
        topdown_count = metadata.get("topdown_count", 0)
        bottomup_count = metadata.get("bottomup_count", 0)

        # Regime display names (English alerts only)
        REGIME_EN = {
            "strong_bull": "Strong Bull", "moderate_bull": "Moderate Bull",
            "sideways": "Sideways", "moderate_bear": "Moderate Bear", "strong_bear": "Strong Bear",
        }
        CHANNEL_EN = {"top-down": "Top-Down (Leading Sector)", "bottom-up": "Bottom-Up (Individual)"}
        if mode == "morning":
            title = "🔔 US Stock Morning Prism Signal Alert"
            time_desc = "10 minutes after market open"
        elif mode == "midday":
            title = "🔔 US Stock Midday Prism Signal Alert"
            time_desc = "at 12:30 PM market time"
        else:
            title = "🔔 US Stock Afternoon Prism Signal Alert"
            time_desc = "after market close"
        header = f"{title}\n📅 {formatted_date} Stocks detected {time_desc}\n"
        volume_label = "Volume Increase"
        gap_label = "Gap Up"
        footer = "📋 Detailed analysis report will be available in 10-30 minutes\n※ This is for investment reference only. Investment decisions are your responsibility."
        channel_map = CHANNEL_EN
        regime_map = REGIME_EN
        score_label = "Score"
        rr_label = "R/R"
        sl_label = "SL"

        message = header

        # Hybrid selection summary (regime + strategy)
        if market_regime and "hybrid" in selection_strategy:
            regime_display = regime_map.get(market_regime, market_regime)
            message += f"🧭 Regime: {regime_display} | Selection: Top-Down {topdown_count} + Bottom-Up {bottomup_count}\n"

        message += "\n"

        for trigger_type, stocks in results.items():
            if trigger_type == "metadata":
                continue

            emoji = self._get_trigger_emoji(trigger_type)
            display_trigger_type = trigger_type
            message += f"{emoji} {display_trigger_type}\n"

            for stock in stocks:
                ticker = stock.get("ticker", stock.get("code", ""))
                name = stock.get("name", ticker)
                current_price = stock.get("current_price", 0)
                change_rate = stock.get("change_rate", 0)

                # Arrow based on change rate
                arrow = "⬆️" if change_rate > 0 else "⬇️" if change_rate < 0 else "➖"

                message += f"· {name} ({ticker})\n"
                message += f"  ${current_price:.2f} {arrow} {abs(change_rate):.2f}%\n"

                # Selection channel tag
                selection_channel = stock.get("selection_channel")
                if selection_channel:
                    channel_display = channel_map.get(selection_channel, selection_channel)
                    message += f"  📌 {channel_display}\n"

                # Trigger-specific data
                if "volume_increase" in stock and "Volume" in trigger_type:
                    volume_increase = stock.get("volume_increase", 0)
                    message += f"  {volume_label}: {volume_increase:.2f}%\n"
                elif "gap_rate" in stock and "Gap" in trigger_type:
                    gap_rate = stock.get("gap_rate", 0)
                    message += f"  {gap_label}: {gap_rate:.2f}%\n"

                # Hybrid scoring details (score, R/R, stop-loss)
                details = []
                final_score = stock.get("final_score")
                if final_score is not None:
                    details.append(f"{score_label}: {final_score:.2f}")
                rr_ratio = stock.get("risk_reward_ratio")
                if rr_ratio is not None:
                    details.append(f"{rr_label}: {rr_ratio:.1f}")
                sl_pct = stock.get("stop_loss_pct")
                if sl_pct is not None:
                    details.append(f"{sl_label}: -{sl_pct:.1f}%")
                if details:
                    message += f"  📊 {' | '.join(details)}\n"

                message += "\n"

        message += footer

        return message

    def _get_trigger_emoji(self, trigger_type: str) -> str:
        """Return emoji matching trigger type"""
        if "Volume" in trigger_type:  # Volume
            return "📊"
        elif "Gap" in trigger_type:  # Gap
            return "📈"
        elif "Value" in trigger_type or "Cap" in trigger_type:  # Market cap
            return "💰"
        elif "Rise" in trigger_type or "Intraday" in trigger_type:  # Rise
            return "🚀"
        elif "Closing" in trigger_type or "Strength" in trigger_type:  # Closing
            return "🔨"
        elif "Sideways" in trigger_type:  # Sideways
            return "↔️"
        else:
            return "🔎"

    async def run_full_pipeline(self, mode: str, language: str = "en", override_date: str = None):
        """
        Execute full US pipeline

        Args:
            mode: 'morning' or 'afternoon'
            language: Legacy language argument forwarded across generation steps.
        """
        logger.info(f"Starting US full pipeline - mode: {mode}")
        tracking_success = True

        try:
            # 0. Run macro intelligence (US market regime, sector data)
            effective_date = override_date if override_date else datetime.now().strftime("%Y%m%d")
            macro_context = await self.run_macro_intelligence(
                reference_date=effective_date,
                language=language
            )
            if macro_context:
                logger.info(f"US macro intelligence: regime={macro_context.get('market_regime')}, "
                           f"sectors={len(macro_context.get('leading_sectors', []))}")
            else:
                logger.warning("US macro intelligence unavailable - proceeding without macro context")

            # 1. Execute trigger batch
            results_file = str(TRIGGER_RESULTS_DIR / f"trigger_results_us_{mode}_{effective_date}.json")
            tickers = await self.run_trigger_batch(mode, macro_context=macro_context, override_date=override_date)

            if not tickers:
                logger.warning("No US stocks selected. Terminating process.")
                return

            # 1-1. Echo trigger snapshot to logs / operator consoles
            if os.path.exists(results_file):
                logger.info(f"US trigger results file confirmed: {results_file}")
                try:
                    with open(results_file, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    metadata = raw.get("metadata", {})
                    trade_date = metadata.get("trade_date", effective_date)
                    all_results = {k: v for k, v in raw.items() if k != "metadata" and isinstance(v, list)}
                    if all_results:
                        all_results["metadata"] = metadata
                        scan_dump = self._create_trigger_alert_message(mode, all_results, trade_date, language)
                        logger.info("Prism trigger scan snapshot:\n%s", scan_dump)
                    else:
                        logger.warning("Trigger results JSON contained no stock lists to summarize.")
                except Exception as exc:
                    logger.warning("Could not format trigger scan log: %s", exc)
            else:
                logger.warning(f"US trigger results file not found: {results_file}")

            # 2. Generate reports
            report_paths = await self.generate_reports(tickers, mode, timeout=600, language=language, macro_context=macro_context)
            if not report_paths:
                logger.warning("No US reports generated. Terminating process.")
                return

            # 3. PDF conversion
            pdf_paths = await self.convert_to_pdf(report_paths)

            # 4. Tracking / trading batch
            if pdf_paths:
                try:
                    logger.info("Starting US stock tracking system batch execution")

                    from prism.ops.pipelines.stock_tracking_agent import USStockTrackingAgent, app as tracking_app

                    async with tracking_app.run():
                        tracking_agent = USStockTrackingAgent()

                        trigger_results_file = str(TRIGGER_RESULTS_DIR / f"trigger_results_us_{mode}_{effective_date}.json")

                        tracking_success = await tracking_agent.run(
                            pdf_paths,
                            language=language,
                            trigger_results_file=trigger_results_file,
                        )

                        if tracking_success:
                            logger.info("US tracking system batch execution complete")
                        else:
                            logger.error("US tracking system batch execution failed")

                except Exception as e:
                    tracking_success = False
                    logger.error(f"Error during US tracking system batch execution: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning("No US reports generated, not executing tracking system batch.")

            if tracking_success:
                logger.info(f"US full pipeline complete - mode: {mode}")
            else:
                logger.warning(f"US full pipeline completed with tracking errors - mode: {mode}")

        except Exception as e:
            logger.error(f"Error during US pipeline execution: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            from prism.core.openai.quota_utils import is_openai_quota_error

            if is_openai_quota_error(e):
                logger.error(
                    "OpenAI quota exhausted — top up credits or adjust organization billing before retrying."
                )


async def main():
    """Main function - command line interface"""
    parser = argparse.ArgumentParser(description="US stock analysis orchestrator")
    parser.add_argument("--mode", choices=["morning", "midday", "afternoon", "both"], default="both",
                        help="Execution mode (morning, midday, afternoon, both)")
    from prism.reporting.translation.languages import SUPPORTED_OUTPUT_LANGUAGES

    parser.add_argument(
        "--language",
        choices=sorted(SUPPORTED_OUTPUT_LANGUAGES),
        default="en",
        help="Report output language (default: en). Non-English uses the translation layer.",
    )
    parser.add_argument("--no-proxy", action="store_true",
                        help="Disable ChatGPT OAuth proxy (use standard OpenAI API key)")
    parser.add_argument("--force", action="store_true",
                        help="Force execution even on market holidays (for testing)")
    parser.add_argument("--date", type=str, default=None,
                        help="Override trade date (YYYYMMDD format, for testing)")

    args = parser.parse_args()

    # ChatGPT OAuth proxy setup
    proxy_started = False
    stop_proxy = None
    if not args.no_proxy and os.getenv("PRISM_OPENAI_AUTH_MODE") == "chatgpt_oauth":
        try:
            _proxy_mod = _import_proxy_safe()
            inject_env = _proxy_mod.inject_env
            start_proxy = _proxy_mod.start_proxy
            clear_env = _proxy_mod.clear_env
            stop_proxy = _proxy_mod.stop_proxy

            inject_env()
            proxy_started = await start_proxy()
            if not proxy_started:
                logger.warning("ChatGPT OAuth proxy failed to start, falling back to standard API")
                clear_env()
        except Exception as e:
            logger.warning("ChatGPT OAuth proxy setup error: %s, falling back to standard API", e)
            try:
                _proxy_mod.clear_env()
            except Exception:
                pass

    orchestrator = USStockAnalysisOrchestrator()

    if args.mode == "morning" or args.mode == "both":
        await orchestrator.run_full_pipeline("morning", language=args.language, override_date=args.date)

    if args.mode == "midday":
        await orchestrator.run_full_pipeline("midday", language=args.language, override_date=args.date)

    if args.mode == "afternoon" or args.mode == "both":
        await orchestrator.run_full_pipeline("afternoon", language=args.language, override_date=args.date)

    # Stop proxy if started
    if proxy_started and stop_proxy is not None:
        try:
            await stop_proxy()
        except Exception:
            pass


def cli_main():
    """Sync console entry point."""
    force_execution = "--force" in sys.argv

    from prism.ops.maintenance.check_market_day import is_us_market_day

    if not force_execution and not is_us_market_day():
        current_date = datetime.now().date()
        logger.info(f"Today ({current_date}) is a US stock market holiday. Not executing batch job.")
        sys.exit(0)

    if force_execution:
        logger.warning("Force execution enabled - ignoring market holiday check")

    import threading

    def exit_after_timeout():
        import time
        import signal
        time.sleep(7200)
        logger.warning("120-minute timeout reached: forcefully terminating process")
        os.kill(os.getpid(), signal.SIGTERM)

    timer_thread = threading.Thread(target=exit_after_timeout, daemon=True)
    timer_thread.start()

    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
