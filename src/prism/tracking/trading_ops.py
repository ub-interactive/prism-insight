"""
Trading Operations for Stock Tracking

Buy/sell decision logic and message formatting.
Extracted from stock_tracking_agent.py for LLM context efficiency.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from prism.tracking.helpers import parse_price_value

logger = logging.getLogger(__name__)


def analyze_sell_decision(stock_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Sell decision analysis.

    Args:
        stock_data: Stock information

    Returns:
        Tuple[bool, str]: Whether to sell, sell reason
    """
    try:
        ticker = stock_data.get('ticker', '')
        buy_price = stock_data.get('buy_price', 0)
        buy_date = stock_data.get('buy_date', '')
        current_price = stock_data.get('current_price', 0)
        target_price = stock_data.get('target_price', 0)
        stop_loss = stock_data.get('stop_loss', 0)

        # Calculate profit rate
        profit_rate = ((current_price - buy_price) / buy_price) * 100

        # Days elapsed from buy date
        buy_datetime = datetime.strptime(buy_date, "%Y-%m-%d %H:%M:%S")
        days_passed = (datetime.now() - buy_datetime).days

        # Extract scenario information
        scenario_str = stock_data.get('scenario', '{}')
        investment_period = "Medium-term"

        try:
            if isinstance(scenario_str, str):
                scenario_data = json.loads(scenario_str)
                investment_period = scenario_data.get('investment_period', 'Medium-term')
        except:
            pass

        # Check stop-loss condition
        if stop_loss > 0 and current_price <= stop_loss:
            return True, f"손절 조건 도달 (손절가: {stop_loss:,.0f}원)"

        # Check target price reached
        if target_price > 0 and current_price >= target_price:
            return True, f"목표가 달성 (목표가: {target_price:,.0f}원)"

        # Sell conditions by investment period
        if investment_period == "Short-term":
            if days_passed >= 15 and profit_rate >= 5:
                return True, f"단기 투자 목표 달성 (보유: {days_passed}일, 수익률: {profit_rate:.2f}%)"
            if days_passed >= 10 and profit_rate <= -3:
                return True, f"단기 투자 손실 방어 (보유: {days_passed}일, 수익률: {profit_rate:.2f}%)"

        # General sell conditions
        if profit_rate >= 10:
            return True, f"수익률 10% 이상 달성 (현재 수익률: {profit_rate:.2f}%)"

        if profit_rate <= -5:
            return True, f"손실 -5% 이상 발생 (현재 수익률: {profit_rate:.2f}%)"

        if days_passed >= 30 and profit_rate < 0:
            return True, f"30일 이상 보유 중 손실 (보유: {days_passed}일, 수익률: {profit_rate:.2f}%)"

        if days_passed >= 60 and profit_rate >= 3:
            return True, f"60일 이상 보유 중 3% 이상 수익 (보유: {days_passed}일, 수익률: {profit_rate:.2f}%)"

        if investment_period == "Long-term" and days_passed >= 90 and profit_rate < 0:
            return True, f"장기 투자 손실 정리 (보유: {days_passed}일, 수익률: {profit_rate:.2f}%)"

        return False, "보유 지속"

    except Exception as e:
        logger.error(f"Error analyzing sell: {str(e)}")
        return False, "분석 오류"


def format_buy_message(
    company_name: str,
    ticker: str,
    current_price: float,
    scenario: Dict[str, Any],
    rank_change_msg: str = ""
) -> str:
    """
    Format buy-trade notification plain text for logs/digests/Firebase-style hooks.

    Args:
        company_name: Company name
        ticker: Stock code
        current_price: Current price
        scenario: Trading scenario
        rank_change_msg: Ranking change message

    Returns:
        str: Formatted message
    """
    message = f"📈 신규 매수: {company_name}({ticker})\n" \
              f"매수가: {current_price:,.0f}원\n" \
              f"목표가: {scenario.get('target_price', 0):,.0f}원\n" \
              f"손절가: {scenario.get('stop_loss', 0):,.0f}원\n" \
              f"투자기간: {scenario.get('investment_period', '단기')}\n" \
              f"산업군: {scenario.get('sector', '알 수 없음')}\n"

    if scenario.get('valuation_analysis'):
        message += f"밸류에이션: {scenario.get('valuation_analysis')}\n"

    if scenario.get('sector_outlook'):
        message += f"업종 전망: {scenario.get('sector_outlook')}\n"

    if rank_change_msg:
        message += f"거래대금 분석: {rank_change_msg}\n"

    message += f"투자근거: {scenario.get('rationale', '정보 없음')}\n"

    # Format trading scenario section
    trading_scenarios = scenario.get('trading_scenarios', {})
    if trading_scenarios and isinstance(trading_scenarios, dict):
        message += _format_trading_scenarios(trading_scenarios, current_price)

    return message


def _format_trading_scenarios(trading_scenarios: Dict[str, Any], current_price: float) -> str:
    """Format trading scenarios section."""
    message = "\n" + "=" * 40 + "\n"
    message += "📋 매매 시나리오\n"
    message += "=" * 40 + "\n\n"

    # Key levels
    key_levels = trading_scenarios.get('key_levels', {})
    if key_levels:
        message += "💰 핵심 가격대:\n"

        primary_resistance = parse_price_value(key_levels.get('primary_resistance', 0))
        secondary_resistance = parse_price_value(key_levels.get('secondary_resistance', 0))
        if primary_resistance or secondary_resistance:
            message += "  📈 저항선:\n"
            if secondary_resistance:
                message += f"    • 2차: {secondary_resistance:,.0f}원\n"
            if primary_resistance:
                message += f"    • 1차: {primary_resistance:,.0f}원\n"

        message += f"  ━━ 현재가: {current_price:,.0f}원 ━━\n"

        primary_support = parse_price_value(key_levels.get('primary_support', 0))
        secondary_support = parse_price_value(key_levels.get('secondary_support', 0))
        if primary_support or secondary_support:
            message += "  📉 지지선:\n"
            if primary_support:
                message += f"    • 1차: {primary_support:,.0f}원\n"
            if secondary_support:
                message += f"    • 2차: {secondary_support:,.0f}원\n"

        volume_baseline = key_levels.get('volume_baseline', '')
        if volume_baseline:
            message += f"  📊 거래량 기준: {volume_baseline}\n"

        message += "\n"

    # Sell triggers
    sell_triggers = trading_scenarios.get('sell_triggers', [])
    if sell_triggers:
        message += "🔔 매도 시그널:\n"
        for trigger in sell_triggers:
            if "profit" in trigger.lower() or "target" in trigger.lower() or "resistance" in trigger.lower():
                emoji = "✅"
            elif "loss" in trigger.lower() or "support" in trigger.lower() or "drop" in trigger.lower():
                emoji = "⛔"
            elif "time" in trigger.lower() or "sideways" in trigger.lower():
                emoji = "⏰"
            else:
                emoji = "•"
            message += f"  {emoji} {trigger}\n"
        message += "\n"

    # Hold conditions
    hold_conditions = trading_scenarios.get('hold_conditions', [])
    if hold_conditions:
        message += "✋ 보유 지속 조건:\n"
        for condition in hold_conditions:
            message += f"  • {condition}\n"
        message += "\n"

    # Portfolio context
    portfolio_context = trading_scenarios.get('portfolio_context', '')
    if portfolio_context:
        message += f"💼 포트폴리오 관점:\n  {portfolio_context}\n"

    return message


def format_sell_message(
    company_name: str,
    ticker: str,
    buy_price: float,
    sell_price: float,
    profit_rate: float,
    holding_days: int,
    sell_reason: str
) -> str:
    """
    Format sell-trade notification plain text for logs/digests/Firebase-style hooks.

    Args:
        company_name: Company name
        ticker: Stock code
        buy_price: Buy price
        sell_price: Sell price
        profit_rate: Profit rate (%)
        holding_days: Holding period (days)
        sell_reason: Sell reason

    Returns:
        str: Formatted message
    """
    arrow = "⬆️" if profit_rate > 0 else "⬇️" if profit_rate < 0 else "➖"
    message = f"📉 매도: {company_name}({ticker})\n" \
              f"매수가: {buy_price:,.0f}원\n" \
              f"매도가: {sell_price:,.0f}원\n" \
              f"수익률: {arrow} {abs(profit_rate):.2f}%\n" \
              f"보유기간: {holding_days}일\n" \
              f"매도이유: {sell_reason}"
    return message


def calculate_profit_rate(buy_price: float, current_price: float) -> float:
    """Calculate profit rate percentage."""
    if buy_price <= 0:
        return 0.0
    return ((current_price - buy_price) / buy_price) * 100


def calculate_holding_days(buy_date: str) -> int:
    """Calculate holding period in days."""
    try:
        buy_datetime = datetime.strptime(buy_date, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - buy_datetime).days
    except:
        return 0
