from mcp_agent.agents.agent import Agent


def create_news_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
) -> Agent:
    instruction = f"""You are a China A-share news analyst for {company_name} ({code}.{exchange}).

Use perplexity to gather recent news (within 1 month of {reference_date}).
Focus on disclosures (公告), policy, sector news, and same-day price drivers.
Cite sources as [Perplexity:N, Date].

Report title: ### 3. Recent Major News Summary
First subsection: #### Analysis of Same-day Stock Price Movement Factors
"""
    return Agent(
        name="cn_news_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "time"],
    )
