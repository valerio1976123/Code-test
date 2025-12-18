from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SupervisedDataset:
    X: pd.DataFrame
    y_cls: pd.Series
    y_ret: pd.Series


def build_ohlcv_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input df must include: timestamp, open, high, low, close, volume
    """
    out = pd.DataFrame(index=df.index)
    out["close"] = df["close"].astype(float)
    out["volume"] = df["volume"].astype(float)

    # Returns
    out["ret_1d"] = out["close"].pct_change(1)
    out["ret_5d"] = out["close"].pct_change(5)
    out["ret_20d"] = out["close"].pct_change(20)

    # Moving averages
    out["sma_5"] = out["close"].rolling(5).mean()
    out["sma_20"] = out["close"].rolling(20).mean()
    out["sma_50"] = out["close"].rolling(50).mean()

    # Price vs MA
    out["close_over_sma_5"] = out["close"] / out["sma_5"] - 1.0
    out["close_over_sma_20"] = out["close"] / out["sma_20"] - 1.0
    out["close_over_sma_50"] = out["close"] / out["sma_50"] - 1.0

    # Volatility
    out["vol_20"] = out["ret_1d"].rolling(20).std()

    # Volume changes
    out["vol_chg_1d"] = out["volume"].pct_change(1)
    out["vol_chg_5d"] = out["volume"].pct_change(5)

    return out


def make_supervised(
    df_ohlcv: pd.DataFrame,
    *,
    horizon_days: int = 1,
    flat_threshold: float = 0.002,
) -> SupervisedDataset:
    """
    Build (X, y_cls, y_ret) from OHLCV data.

    y_ret: next-period return over horizon_days (float)
    y_cls: {-1, 0, +1} based on flat_threshold
    """
    feats = build_ohlcv_features(df_ohlcv)
    fut_close = df_ohlcv["close"].shift(-horizon_days).astype(float)
    y_ret = (fut_close / df_ohlcv["close"].astype(float) - 1.0).rename("y_ret")

    y_cls = pd.Series(0, index=y_ret.index, name="y_cls")
    y_cls = y_cls.where(~(y_ret > flat_threshold), 1)
    y_cls = y_cls.where(~(y_ret < -flat_threshold), -1)

    X = feats.dropna()
    y_cls = y_cls.loc[X.index]
    y_ret = y_ret.loc[X.index]

    # Drop last horizon rows that have no target
    valid = y_ret.notna()
    X = X.loc[valid]
    y_cls = y_cls.loc[valid]
    y_ret = y_ret.loc[valid]

    # Remove raw columns we don't want as features
    X = X.drop(columns=["close", "volume"], errors="ignore")
    return SupervisedDataset(X=X, y_cls=y_cls, y_ret=y_ret)

