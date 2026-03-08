"""
Test suite for backtest engine
"""

import pytest
import pandas as pd
import numpy as np
from prepare import backtest, _calculate_metrics
from strategy import Strategy


@pytest.fixture
def sample_backtest_data():
    """Create sample data with signals for backtest"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    close = 100 + np.cumsum(np.random.randn(100) * 0.5)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': close,
        'high': close + abs(np.random.randn(100) * 0.2),
        'low': close - abs(np.random.randn(100) * 0.2),
        'close': close,
        'volume': np.random.randint(1000, 10000, 100)
    })

    # Add required indicators
    df['atr_14'] = abs(np.random.randn(100) * 2)
    df['momentum_5'] = df['close'].pct_change(5)

    return df


def test_calculate_metrics_empty_trades():
    """Test metrics calculation with no trades"""
    equity_curve = []
    trades = []
    metrics = _calculate_metrics(equity_curve, trades, 10000)

    assert metrics['sharpe_ratio'] == 0
    assert metrics['max_drawdown'] == 0
    assert metrics['win_rate'] == 0
    assert metrics['trades'] == 0
    assert metrics['final_capital'] == 10000


def test_calculate_metrics_valid_trades():
    """Test metrics calculation with valid equity curve"""
    equity_curve = [10000, 10100, 10050, 10200, 10150]
    trades = [
        {'type': 'buy', 'price': 100, 'cost': 0.001},
        {'type': 'sell', 'price': 105, 'cost': 0.001}
    ]
    metrics = _calculate_metrics(equity_curve, trades, 10000)

    assert isinstance(metrics['sharpe_ratio'], float)
    assert isinstance(metrics['max_drawdown'], float)
    assert 0 <= metrics['max_drawdown'] <= 1
    assert metrics['trades'] == 2
    assert metrics['final_capital'] == 10150


def test_backtest_returns_valid_metrics(sample_backtest_data):
    """Test backtest returns all required metrics"""
    strategy = Strategy()
    metrics = backtest(strategy, sample_backtest_data, initial_capital=10000)

    # Check all required keys exist
    required_keys = ['sharpe_ratio', 'max_drawdown', 'win_rate', 'total_return', 'trades', 'final_capital']
    for key in required_keys:
        assert key in metrics

    # Check value types and ranges
    assert isinstance(metrics['sharpe_ratio'], (int, float))
    assert isinstance(metrics['max_drawdown'], (int, float))
    assert 0 <= metrics['win_rate'] <= 1
    assert isinstance(metrics['trades'], int)
    assert metrics['trades'] >= 0


def test_backtest_preserves_capital(sample_backtest_data):
    """Test backtest doesn't create or destroy capital incorrectly"""
    strategy = Strategy()
    metrics = backtest(strategy, sample_backtest_data, initial_capital=10000)

    # Final capital should be positive
    assert metrics['final_capital'] > 0
    # Total return should be reasonable (not 1000x or -100%)
    assert -1 < metrics['total_return'] < 10

