from mcp_agent.agents.agent import Agent


def create_news_analysis_agent(
    company_name: str,
    code: str,
    exchange: str,
    reference_date: str,
    language: str = "en",
) -> Agent:
    ref_date = f"{reference_date[:4]}-{reference_date[4:6]}-{reference_date[6:]}"
    instruction = f"""You are a China A-share news analyst for {company_name} ({code}.{exchange}).

Use perplexity to gather recent news (within 1 month of {reference_date}).
Always embed "As of {ref_date}" in perplexity queries.
Search using the Chinese company name "{company_name}" plus A-share context ({code}.{exchange}).
Beware perplexity hallucinations: verify dates against {reference_date}; reject news outside the 1-month window.
If no material news is found, state that clearly — do not invent events.

Focus on disclosures (公告), policy, sector news, and same-day price drivers.
Cite sources as [Perplexity:N, Date].

## Report Structure
- Start with \\n\\n before the title
- Sub-sections use #### headings
Report title: ### 3. Recent Major News Summary
First subsection: #### Analysis of Same-day Stock Price Movement Factors
"""
    return Agent(
        name="cn_news_analysis_agent",
        instruction=instruction,
        server_names=["perplexity", "time"],
    )
