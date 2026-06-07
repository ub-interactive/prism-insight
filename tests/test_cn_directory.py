from prism.core.cn.agents.directory import get_agent_directory


def test_builds_all_six_agents():
    agents = get_agent_directory(
        company_name="贵州茅台",
        code="600519",
        exchange="SH",
        reference_date="20260606",
        base_sections=[
            "price_volume_analysis",
            "institutional_holdings_analysis",
            "company_status",
            "company_overview",
            "news_analysis",
            "market_index_analysis",
        ],
        language="zh",
        prefetched_data={"stock_ohlcv": "md", "holder_info": "md", "market_indices": {"csi300": "md"}},
    )
    assert len(agents) == 6
    assert "price_volume_analysis" in agents
    assert "market_index_analysis" in agents
