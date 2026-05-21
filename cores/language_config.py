"""
Language Configuration Module

English-only language configuration and translation management
for the PRISM-INSIGHT stock analysis system.
"""

import os
from enum import Enum
from datetime import datetime
from typing import Dict, Any


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"


class LanguageConfig:
    """
    Centralized language configuration and translation management

    This class provides all language-specific strings, templates, and formatting
    used throughout the PRISM-INSIGHT system.
    """

    def __init__(self, language: Language = Language.ENGLISH):
        """
        Initialize language configuration

        Args:
            language: Target language (default: English)
        """
        self.language = language

    def get_report_sections(self) -> Dict[str, str]:
        """
        Get report section titles in the specified language

        Returns:
            Dictionary mapping section keys to localized titles
        """
        return {
            "price_volume_analysis": "Price and Volume Analysis",
            "investor_trading_analysis": "Investor Trading Trends Analysis",
            "company_status": "Company Status",
            "company_overview": "Company Overview",
            "news_analysis": "News Analysis",
            "market_index_analysis": "Market Analysis",
            "investment_strategy": "Investment Strategy and Opinion",
            "executive_summary": "Executive Summary"
        }

    def get_telegram_template(self) -> Dict[str, str]:
        """
        Get Telegram message templates in the specified language

        Returns:
            Dictionary of Telegram message templates
        """
        return {
            # Alert titles
            "alert_title_morning": "🌅 Morning Buy Signal Alert",
            "alert_title_afternoon": "🌆 Afternoon Buy Signal Alert",

            # Time descriptions
            "time_desc_morning": "10 minutes after market open",
            "time_desc_afternoon": "10 minutes after lunch break",

            # Message templates
            "detected_stocks": "📊 Buy signals detected on {date} ({time_desc})",
            "total_stocks": "Total: {count} stocks",
            "no_signals": "No buy signals detected today.",

            # Report sections
            "buy_score": "Buy Score",
            "current_price": "Current Price",
            "target_price": "Target Price",
            "stop_loss": "Stop Loss",
            "investment_period": "Investment Period",
            "sector": "Sector",
            "rationale": "Investment Rationale",

            # Disclaimers
            "disclaimer_title": "📝 Important Notice",
            "disclaimer_simulation": "This report is an AI-based simulation result and is not related to actual trading.",
            "disclaimer_reference": "This information is for reference only. All investment decisions and responsibilities lie solely with the investor.",
            "disclaimer_not_recommendation": "This is not a leading channel and does not recommend buying/selling specific stocks.",

            # Portfolio summary
            "portfolio_summary_title": "📊 PRISM Simulator | Real-time Portfolio",
            "current_holdings": "Current Holdings",
            "best_performer": "Best Performer",
            "worst_performer": "Worst Performer",
            "sector_distribution": "Sector Distribution",
            "trading_history": "Trading History Stats",
            "total_trades": "Total Trades",
            "profitable_trades": "Profitable Trades",
            "losing_trades": "Losing Trades",
            "win_rate": "Win Rate",
            "cumulative_return": "Cumulative Return",

            # Chart labels
            "chart_title_price": "Price Chart",
            "chart_title_volume": "Trading Volume",

            # Investment periods
            "period_short": "Short-term",
            "period_medium": "Mid-term",
            "period_long": "Long-term",

            # Date format
            "date_format": "%B %d, %Y"  # January 15, 2024
        }

    def get_chart_labels(self) -> Dict[str, str]:
        """
        Get chart labels in the specified language

        Returns:
            Dictionary of chart labels
        """
        return {
            "date": "Date",
            "price": "Price (KRW)",
            "volume": "Volume",
            "market_cap": "Market Cap (KRW Billion)",
            "per": "PER",
            "pbr": "PBR",
            "roe": "ROE (%)",
            "debt_ratio": "Debt Ratio (%)",
            "operating_margin": "Operating Margin (%)",
            "net_margin": "Net Margin (%)",
            "price_chart": "Stock Price Chart",
            "volume_chart": "Trading Volume Chart",
            "fundamental_chart": "Fundamental Analysis",
            "moving_average_5": "5-day MA",
            "moving_average_20": "20-day MA",
            "moving_average_60": "60-day MA",
            "moving_average_120": "120-day MA",
            "support_level": "Support Level",
            "resistance_level": "Resistance Level"
        }

    def format_date(self, date_str: str) -> str:
        """
        Format date string according to language preference

        Args:
            date_str: Date string in YYYYMMDD format

        Returns:
            Formatted date string
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            templates = self.get_telegram_template()
            return date_obj.strftime(templates["date_format"])
        except:
            return date_str

    def get_trigger_emojis(self) -> Dict[str, str]:
        """
        Get emoji mappings for different trigger types

        These are universal across languages

        Returns:
            Dictionary mapping trigger types to emojis
        """
        return {
            "profit_target": "✅",
            "stop_loss": "⛔",
            "time_condition": "⏰",
            "momentum_exhaustion": "📉",
            "resistance": "🔝",
            "support": "🔻",
            "trend_reversal": "🔄",
            "buy": "📈",
            "sell": "📉",
            "hold": "✋",
            "caution": "⚠️",
            "info": "ℹ️",
            "success": "✓",
            "error": "✗",
            "morning": "🌅",
            "afternoon": "🌆",
            "portfolio": "💼"
        }

    def get_analysis_terminology(self) -> Dict[str, str]:
        """
        Get analysis terminology translations

        Returns:
            Dictionary of analysis terms
        """
        return {
            "technical_analysis": "Technical Analysis",
            "fundamental_analysis": "Fundamental Analysis",
            "valuation": "Valuation",
            "momentum": "Momentum",
            "trend": "Trend",
            "support": "Support",
            "resistance": "Resistance",
            "breakout": "Breakout",
            "consolidation": "Consolidation",
            "overbought": "Overbought",
            "oversold": "Oversold",
            "bullish": "Bullish",
            "bearish": "Bearish",
            "neutral": "Neutral",
            "uptrend": "Uptrend",
            "downtrend": "Downtrend",
            "sideways": "Sideways",
            "volatility": "Volatility",
            "liquidity": "Liquidity",
            "market_cap": "Market Capitalization",
            "pe_ratio": "Price-to-Earnings Ratio (PER)",
            "pb_ratio": "Price-to-Book Ratio (PBR)",
            "dividend_yield": "Dividend Yield",
            "earnings_growth": "Earnings Growth",
            "revenue_growth": "Revenue Growth"
        }


def get_language_from_env() -> Language:
    """
    Get language setting from environment variable

    Reads PRISM_LANGUAGE environment variable.
    Defaults to English if not set or invalid.

    Returns:
        Language enum value
    """
    lang_str = os.getenv("PRISM_LANGUAGE", "en").lower()

    try:
        return Language(lang_str)
    except ValueError:
        # Default to English if invalid language specified
        return Language.ENGLISH


# Convenience function for getting config
def get_config(language: str = None) -> LanguageConfig:
    """
    Get language configuration instance

    Args:
        language: Language code ("en"). If None, reads from environment.

    Returns:
        LanguageConfig instance
    """
    if language is None:
        lang = get_language_from_env()
    else:
        try:
            lang = Language(language)
        except ValueError:
            lang = Language.ENGLISH

    return LanguageConfig(lang)
