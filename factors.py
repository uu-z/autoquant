"""
Factor Library - Standardized factor interface

Each factor:
- Returns a signal Series (-1, 0, 1)
- Can be evaluated by IC (Information Coefficient)
- Version controlled and composable
"""

import pandas as pd
import numpy as np
from typing import Optional


class Factor:
    """Base factor class"""

    def __init__(self, name: Optional[str] = None) -> None:
        self.name = name or self.__class__.__name__

    def _require_columns(self, df: pd.DataFrame, cols: list) -> None:
        """Validate required columns exist in DataFrame"""
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}: Missing required columns: {missing}")

    def compute(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute factor signal

        Args:
            df: DataFrame with OHLCV + precomputed indicators

        Returns:
            Series: Signal values (-1, 0, 1)
        """
        raise NotImplementedError

    def ic(self, df: pd.DataFrame, forward_periods: int = 5) -> float:
        """
        Calculate Information Coefficient

        IC measures correlation between factor signal and future returns.
        Higher |IC| = better predictive power

        Returns:
            float: IC value (-1 to 1)
        """
        signal = self.compute(df)
        forward_return = df['close'].pct_change(forward_periods).shift(-forward_periods)

        # Remove NaN
        valid = ~(signal.isna() | forward_return.isna())
        if valid.sum() < 10:
            return 0.0

        return signal[valid].corr(forward_return[valid])


class MACrossover(Factor):
    """Moving Average Crossover"""

    def __init__(self, fast: int = 20, slow: int = 60) -> None:
        super().__init__(f"MA_{fast}_{slow}")
        self.fast = fast
        self.slow = slow

    def compute(self, df: pd.DataFrame) -> pd.Series:
        # Use precomputed or calculate
        if f'sma_{self.fast}' in df.columns:
            ma_fast = df[f'sma_{self.fast}']
        else:
            ma_fast = df['close'].rolling(self.fast).mean()

        if f'sma_{self.slow}' in df.columns:
            ma_slow = df[f'sma_{self.slow}']
        else:
            ma_slow = df['close'].rolling(self.slow).mean()

        signal = pd.Series(0, index=df.index)
        signal[ma_fast > ma_slow] = 1
        signal[ma_fast < ma_slow] = -1
        return signal


class RSIFilter(Factor):
    """RSI Overbought/Oversold Filter"""

    def __init__(self, window: int = 14, upper: int = 70, lower: int = 30) -> None:
        super().__init__(f"RSI_{window}_{upper}_{lower}")
        self.window = window
        self.upper = upper
        self.lower = lower

    def compute(self, df: pd.DataFrame) -> pd.Series:
        self._require_columns(df, [f'rsi_{self.window}'])
        rsi = df[f'rsi_{self.window}']

        signal = pd.Series(0, index=df.index)
        signal[rsi < self.lower] = 1   # Oversold: buy
        signal[rsi > self.upper] = -1  # Overbought: sell
        return signal


class MomentumFilter(Factor):
    """Price Momentum Filter"""

    def __init__(self, window: int = 5, threshold: float = 0.02) -> None:
        super().__init__(f"Momentum_{window}_{threshold}")
        self.window = window
        self.threshold = threshold

    def compute(self, df: pd.DataFrame) -> pd.Series:
        self._require_columns(df, [f'momentum_{self.window}'])
        momentum = df[f'momentum_{self.window}']

        signal = pd.Series(0, index=df.index)
        signal[momentum > self.threshold] = 1
        signal[momentum < -self.threshold] = -1
        return signal


class VolatilityFilter(Factor):
    """ATR-based Volatility Filter"""

    def __init__(self, threshold: float = 0.03) -> None:
        super().__init__(f"Volatility_{threshold}")
        self.threshold = threshold

    def compute(self, df: pd.DataFrame) -> pd.Series:
        self._require_columns(df, ['atr_14', 'close'])
        atr_pct = df['atr_14'] / df['close']

        # High volatility: reduce exposure
        signal = pd.Series(1, index=df.index)
        signal[atr_pct > self.threshold] = 0
        return signal


class BollingerBands(Factor):
    """Bollinger Bands Mean Reversion"""

    def __init__(self, window: int = 20) -> None:
        super().__init__(f"BB_{window}")
        self.window = window

    def compute(self, df: pd.DataFrame) -> pd.Series:
        self._require_columns(df, [f'bb_upper_{self.window}', f'bb_lower_{self.window}', 'close'])

        bb_upper = df[f'bb_upper_{self.window}']
        bb_lower = df[f'bb_lower_{self.window}']
        close = df['close']

        signal = pd.Series(0, index=df.index)
        signal[close < bb_lower] = 1   # Below lower band: buy
        signal[close > bb_upper] = -1  # Above upper band: sell
        return signal


class FactorCombiner:
    """Combine multiple factors with weights"""

    def __init__(self, factors, weights=None, method='weighted'):
        """
        Args:
            factors: List of Factor instances
            weights: List of weights (default: equal weight)
            method: 'weighted' or 'vote'
        """
        self.factors = factors
        self.weights = weights or [1.0 / len(factors)] * len(factors)
        self.method = method

        assert len(self.factors) == len(self.weights)
        assert abs(sum(self.weights) - 1.0) < 1e-6

    def compute(self, df):
        """Combine factor signals"""
        signals = [f.compute(df) for f in self.factors]

        if self.method == 'weighted':
            # Weighted average
            combined = sum(s * w for s, w in zip(signals, self.weights))
            # Threshold to -1, 0, 1
            result = pd.Series(0, index=df.index)
            result[combined > 0.3] = 1
            result[combined < -0.3] = -1
            return result

        elif self.method == 'vote':
            # Majority vote
            combined = sum(signals)
            result = pd.Series(0, index=df.index)
            result[combined > 0] = 1
            result[combined < 0] = -1
            return result

    def ic(self, df, forward_periods=5):
        """IC of combined factor"""
        signal = self.compute(df)
        forward_return = df['close'].pct_change(forward_periods).shift(-forward_periods)
        valid = ~(signal.isna() | forward_return.isna())
        if valid.sum() < 10:
            return 0.0
        return signal[valid].corr(forward_return[valid])
