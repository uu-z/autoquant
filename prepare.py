#!/usr/bin/env python3
"""
AutoQuant backtest engine and utilities.
This file is read-only - AI agents should not modify it.

Usage:
    python prepare.py run --mode fast    # Run backtest (30 days)
    python prepare.py run --mode full    # Run backtest (1 year)
    python prepare.py best               # Show best result
"""

import ccxt
import pandas as pd
import numpy as np
import argparse
import importlib.util

# Trading costs
MAKER_FEE = 0.0002  # 0.02% Binance maker fee
TAKER_FEE = 0.0004  # 0.04% Binance taker fee
BASE_SLIPPAGE = 0.0005  # 0.05% base slippage

# Indicator windows
SMA_WINDOWS = [5, 10, 15, 20, 25, 30, 50, 60, 100, 200]
EMA_WINDOWS = [12, 26]
RSI_WINDOWS = [7, 10, 14, 21]
ATR_WINDOWS = [14]
BB_WINDOWS = [20, 30]

def _add_moving_averages(df):
    """Add SMA and EMA indicators"""
    for window in SMA_WINDOWS:
        df[f'sma_{window}'] = df['close'].rolling(window).mean()
        df[f'ema_{window}'] = df['close'].ewm(span=window).mean()

    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    return df

def _add_oscillators(df):
    """Add RSI and momentum indicators"""
    # RSI (multiple windows) - compute delta once
    delta = df['close'].diff()
    for window in RSI_WINDOWS:
        gain = (delta.where(delta > 0, 0)).rolling(window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
        rs = gain / loss
        df[f'rsi_{window}'] = 100 - (100 / (1 + rs))

    # Price momentum
    for window in [3, 5, 10, 20]:
        df[f'momentum_{window}'] = df['close'].pct_change(window)

    # Stochastic
    low_14 = df['low'].rolling(14).min()
    high_14 = df['high'].rolling(14).max()
    df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()
    return df

def _add_volatility_indicators(df):
    """Add Bollinger Bands, ATR, and volume indicators"""
    # Bollinger Bands
    for window in BB_WINDOWS:
        df[f'bb_mid_{window}'] = df['close'].rolling(window).mean()
        df[f'bb_std_{window}'] = df['close'].rolling(window).std()
        df[f'bb_upper_{window}'] = df[f'bb_mid_{window}'] + 2 * df[f'bb_std_{window}']
        df[f'bb_lower_{window}'] = df[f'bb_mid_{window}'] - 2 * df[f'bb_std_{window}']

    # ATR (volatility)
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = high_low.combine(high_close, max).combine(low_close, max)
    df['atr_14'] = tr.rolling(14).mean()

    # Volume indicators
    df['volume_sma_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_20']
    return df

def enrich_data(df):
    """Precompute common technical indicators for strategy to use"""
    df = _add_moving_averages(df)
    df = _add_oscillators(df)
    df = _add_volatility_indicators(df)
    return df

def fetch_data(symbol='BTC/USDT', timeframe='1h', limit=720):
    """Fetch OHLCV data from Binance and enrich with indicators"""
    try:
        exchange = ccxt.binance()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = enrich_data(df)
        return df
    except ccxt.NetworkError as e:
        raise RuntimeError(f"Network error fetching {symbol}: {e}")
    except ccxt.ExchangeError as e:
        raise RuntimeError(f"Exchange error fetching {symbol}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error fetching {symbol}: {e}")

def walk_forward_validation(strategy_instance, df, train_ratio=0.7, n_splits=3):
    """
    Walk-forward validation to prevent overfitting.

    Returns:
        dict: Aggregated metrics across all test periods
    """
    total_len = len(df)
    train_size = int(total_len * train_ratio)
    test_size = (total_len - train_size) // n_splits

    all_metrics = []

    for i in range(n_splits):
        test_start = train_size + i * test_size
        test_end = test_start + test_size

        if test_end > total_len:
            break

        test_df = df.iloc[test_start:test_end].copy()
        metrics = backtest(strategy_instance, test_df)
        all_metrics.append(metrics)

    # Aggregate metrics
    if not all_metrics:
        return None

    avg_metrics = {
        'sharpe_ratio': np.mean([m['sharpe_ratio'] for m in all_metrics]),
        'max_drawdown': np.mean([m['max_drawdown'] for m in all_metrics]),
        'win_rate': np.mean([m['win_rate'] for m in all_metrics]),
        'total_return': np.mean([m['total_return'] for m in all_metrics]),
        'trades': sum([m['trades'] for m in all_metrics]),
        'final_capital': all_metrics[-1]['final_capital'],
        'std_sharpe': np.std([m['sharpe_ratio'] for m in all_metrics]),
        'n_splits': len(all_metrics)
    }

    return avg_metrics

def _execute_trade(signal, position, capital, position_size, row, price, strategy_instance, df_slice, trades, equity_curve):
    """Execute a single trade with realistic costs"""
    if signal == 1 and position == 0:
        # Market impact: larger orders = more slippage
        volume_ratio = (capital * position_size) / (row['volume'] * price) if row['volume'] > 0 else 0
        market_impact = BASE_SLIPPAGE * (1 + volume_ratio * 10)

        total_cost = TAKER_FEE + market_impact
        buy_price = price * (1 + total_cost)

        position = (capital * position_size) / buy_price
        capital -= capital * position_size
        trade = {'type': 'buy', 'price': buy_price, 'time': row['timestamp'], 'cost': total_cost}
        trades.append(trade)
        if hasattr(strategy_instance, 'on_trade'):
            strategy_instance.on_trade(trade, df_slice)

    elif signal == -1 and position > 0:
        volume_ratio = (position * price) / (row['volume'] * price) if row['volume'] > 0 else 0
        market_impact = BASE_SLIPPAGE * (1 + volume_ratio * 10)

        total_cost = TAKER_FEE + market_impact
        sell_price = price * (1 - total_cost)

        capital += position * sell_price
        position = 0
        trade = {'type': 'sell', 'price': sell_price, 'time': row['timestamp'], 'cost': total_cost}
        trades.append(trade)
        if hasattr(strategy_instance, 'on_trade'):
            strategy_instance.on_trade(trade, df_slice)

    return capital, position

def _calculate_metrics(equity_curve, trades, initial_capital):
    """Calculate backtest performance metrics"""
    if len(equity_curve) == 0:
        return {
            'sharpe_ratio': 0, 'max_drawdown': 0, 'win_rate': 0,
            'total_return': 0, 'trades': 0, 'final_capital': initial_capital, 'avg_cost': 0
        }

    equity_curve = np.array(equity_curve)
    returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(365 * 24) if np.std(returns) > 0 else 0
    max_drawdown = np.max(np.maximum.accumulate(equity_curve) - equity_curve) / np.max(equity_curve) if np.max(equity_curve) > 0 else 0
    winning_trades = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1]['price'] > trades[i]['price'])
    win_rate = winning_trades / (len(trades) / 2) if len(trades) > 0 else 0

    total_costs = sum(t.get('cost', 0) for t in trades) * initial_capital / len(trades) if trades else 0

    return {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_return': (equity_curve[-1] - initial_capital) / initial_capital,
        'trades': len(trades),
        'final_capital': equity_curve[-1],
        'avg_cost': total_costs
    }

def backtest(strategy_instance, df, initial_capital=10000):
    """Execute backtest with enhanced strategy interface"""
    df = df.copy()

    # Initialize strategy
    if hasattr(strategy_instance, 'initialize'):
        strategy_instance.initialize(df, initial_capital)

    # Compute factors
    df = strategy_instance.compute_factors(df)
    df = strategy_instance.generate_signals(df)

    # Simulate trading
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        signal = row['signal']
        price = row['close']

        # Get position size (pass current state)
        position_size = strategy_instance.position_sizing(
            df.iloc[:i+1], capital, position,
            {'trades': trades, 'equity': equity_curve}
        )

        # Execute trades
        capital, position = _execute_trade(
            signal, position, capital, position_size, row, price,
            strategy_instance, df.iloc[:i+1], trades, equity_curve
        )

        equity = capital + position * price
        equity_curve.append(equity)

    # Calculate metrics
    return _calculate_metrics(equity_curve, trades, initial_capital)

def calculate_score(metrics):
    """Calculate composite score"""
    return (
        metrics['sharpe_ratio'] * 0.5
        - metrics['max_drawdown'] * 0.3
        + metrics['win_rate'] * 0.2
    )

def load_strategy():
    """Dynamically load strategy.py"""
    spec = importlib.util.spec_from_file_location("strategy", "strategy.py")
    strategy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy)
    return strategy.Strategy() if hasattr(strategy, 'Strategy') else strategy

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['run', 'best', 'validate'])
    parser.add_argument('--mode', choices=['fast', 'full'], default='fast')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading pair')
    args = parser.parse_args()

    if args.command == 'run':
        limit = 720 if args.mode == 'fast' else 8760
        print(f"Fetching {limit} hours of {args.symbol} data...")
        df = fetch_data(symbol=args.symbol, limit=limit)
        strategy = load_strategy()
        metrics = backtest(strategy, df)
        score = calculate_score(metrics)
        print(f"\nResults:")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.3f}")
        print(f"  Win Rate: {metrics['win_rate']:.3f}")
        print(f"  Total Return: {metrics['total_return']:.2%}")
        print(f"  Trades: {metrics['trades']}")
        print(f"  Score: {score:.3f}")

    elif args.command == 'validate':
        # Walk-forward validation (防过拟合)
        limit = 2160 if args.mode == 'fast' else 8760  # 3x data for validation
        print(f"Walk-forward validation on {limit} hours of {args.symbol} data...")
        df = fetch_data(symbol=args.symbol, limit=limit)
        strategy = load_strategy()
        metrics = walk_forward_validation(strategy, df, train_ratio=0.7, n_splits=3)

        if metrics:
            score = calculate_score(metrics)
            print(f"\nValidation Results (avg across {metrics['n_splits']} periods):")
            print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f} ± {metrics['std_sharpe']:.3f}")
            print(f"  Max Drawdown: {metrics['max_drawdown']:.3f}")
            print(f"  Win Rate: {metrics['win_rate']:.3f}")
            print(f"  Total Return: {metrics['total_return']:.2%}")
            print(f"  Trades: {metrics['trades']}")
            print(f"  Score: {score:.3f}")
        else:
            print("Validation failed")

    elif args.command == 'best':
        try:
            df = pd.read_csv('results.tsv', sep='\t')
            kept = df[df['status'] == 'keep']
            if len(kept) > 0:
                best = kept.loc[kept['score'].idxmax()]
                print(f"Best Score: {best['score']:.6f}")
                print(f"  Commit: {best['commit']}")
                print(f"  Description: {best['description']}")
            else:
                print("No experiments found")
        except FileNotFoundError:
            print("No experiments found")

