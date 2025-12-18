from __future__ import annotations

import pandas as pd

from app.market.prediction.feature_engineering import make_supervised


def test_make_supervised_shapes() -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=200, freq="D"),
            "open": [100 + i * 0.1 for i in range(200)],
            "high": [101 + i * 0.1 for i in range(200)],
            "low": [99 + i * 0.1 for i in range(200)],
            "close": [100 + i * 0.1 for i in range(200)],
            "volume": [1_000_000 + i * 1000 for i in range(200)],
        }
    )

    ds = make_supervised(df, horizon_days=1)
    assert ds.X.shape[0] > 50
    assert ds.X.shape[0] == ds.y_cls.shape[0] == ds.y_ret.shape[0]
    # Must not contain NaNs
    assert ds.X.isna().sum().sum() == 0

