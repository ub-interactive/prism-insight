from mcp_agent.agents.agent import Agent


def create_market_index_analysis_agent(
    reference_date: str,
    max_years_ago: str,
    max_years: int,
    language: str = "en",
    prefetched_indices: str | None = None,
) -> Agent:
    instruction = f"""You are a China A-share market strategist.

## Pre-collected Index Data
{prefetched_indices or "_No index data provided._"}

Analyze 上证指数, 深证成指, 创业板指, 沪深300 impact on A-share sentiment.
Use perplexity for same-day macro/news catalysts if needed.

Report title: ### 4. Market Analysis
First subsection: #### Same-day Market Movement Factor Analysis
Analysis date: {reference_date}
"""
    return Agent(
        name="cn_market_index_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "time"],
    )
