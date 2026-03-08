"""
Test suite for factor library
"""

import pytest
import pandas as pd
import numpy as np
from factors import MACrossover, RSIFilter, MomentumFilter, BollingerBands


@pytest.fixture
def sample_data():
    """Create sample OHLCV data for testing"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    close = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': close + np.random.randn(100) * 0.1,
        'high': close + abs(np.random.randn(100) * 0.2),
        'low': close - abs(np.random.randn(100) * 0.2),
        'close': close,
        'volume': np.random.randint(1000, 10000, 100)
    })

    # Add precomputed indicators
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    df['rsi_14'] = 50 + np.random.randn(100) * 15  # Mock RSI
    df['momentum_5'] = df['close'].pct_change(5)
    df['bb_upper_20'] = df['close'].rolling(20).mean() + 2 * df['close'].rolling(20).std()
    df['bb_lower_20'] = df['close'].rolling(20).mean() - 2 * df['close'].rolling(20).std()

    return df


def test_ma_crossover_signal(sample_data):
    """Test MA crossover generates valid signals"""
    factor = MACrossover(10, 20)
    signal = factor.compute(sample_data)

    # Check signal values are valid
    assert signal.isin([-1, 0, 1]).all()
    # Check signal is a Series
    assert isinstance(signal, pd.Series)
    # Check length matches input
    assert len(signal) == len(sample_data)


def test_rsi_filter_signal(sample_data):
    """Test RSI filter generates valid signals"""
    factor = RSIFilter(14, 70, 30)
    signal = factor.compute(sample_data)

    assert signal.isin([-1, 0, 1]).all()
    assert isinstance(signal, pd.Series)


def test_momentum_filter_signal(sample_data):
    """Test momentum filter generates valid signals"""
    factor = MomentumFilter(5, 0.02)
    signal = factor.compute(sample_data)

    assert signal.isin([-1, 0, 1]).all()
    assert isinstance(signal, pd.Series)


def test_factor_ic_calculation(sample_data):
    """Test IC calculation returns valid correlation"""
    factor = MACrossover(10, 20)
    ic = factor.ic(sample_data, forward_periods=5)

    # IC should be between -1 and 1
    assert -1 <= ic <= 1
    assert isinstance(ic, float)


def test_bollinger_bands_signal(sample_data):
    """Test Bollinger Bands generates valid signals"""
    factor = BollingerBands(20)
    signal = factor.compute(sample_data)

    assert signal.isin([-1, 0, 1]).all()
    assert isinstance(signal, pd.Series)

