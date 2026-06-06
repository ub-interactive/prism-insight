import pandas as pd

from prism.core.visualization.cn_chart import _resolve_holder_columns


def test_resolve_holder_columns_prefers_shareholding_ratio_over_rank():
    df = pd.DataFrame({
        "名次": [1, 2],
        "股东名称": ["A", "B"],
        "占总股本持股比例": [10.5, 8.2],
    })
    assert _resolve_holder_columns(df) == ("股东名称", "占总股本持股比例")
