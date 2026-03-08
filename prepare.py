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

def fetch_data(symbol='BTC/USDT', timeframe='1h', limit=720):
    """Fetch OHLCV data from Binance"""
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def backtest(strategy_module, df, initial_capital=10000):
    """Execute backtest and calculate metrics"""
    df = df.copy()

    # Call strategy functions
    df = strategy_module.compute_factors(df)
    df = strategy_module.generate_signals(df)
    df = strategy_module.position_sizing(df, initial_capital)

    # Simulate trading
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        signal = row['signal']
        price = row['close']
        position_size = row['position_size']

        # Execute trades (0.1% slippage)
        if signal == 1 and position == 0:  # Buy
            slippage = 0.001
            buy_price = price * (1 + slippage)
            position = (capital * position_size) / buy_price
            capital -= capital * position_size
            trades.append({'type': 'buy', 'price': buy_price, 'time': row['timestamp']})

        elif signal == -1 and position > 0:  # Sell
            slippage = 0.001
            sell_price = price * (1 - slippage)
            capital += position * sell_price
            position = 0
            trades.append({'type': 'sell', 'price': sell_price, 'time': row['timestamp']})

        # Record equity
        equity = capital + position * price
        equity_curve.append(equity)

    # Calculate metrics
    equity_curve = np.array(equity_curve)
    returns = np.diff(equity_curve) / equity_curve[:-1]

    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(365 * 24) if np.std(returns) > 0 else 0
    max_drawdown = np.max(np.maximum.accumulate(equity_curve) - equity_curve) / np.max(equity_curve)

    winning_trades = sum(1 for i in range(0, len(trades)-1, 2) if i+1 < len(trades) and trades[i+1]['price'] > trades[i]['price'])
    win_rate = winning_trades / (len(trades) / 2) if len(trades) > 0 else 0

    return {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_return': (equity_curve[-1] - initial_capital) / initial_capital,
        'trades': len(trades),
        'final_capital': equity_curve[-1]
    }

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
    return strategy

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['run', 'best'])
    parser.add_argument('--mode', choices=['fast', 'full'], default='fast')
    args = parser.parse_args()

    if args.command == 'run':
        limit = 720 if args.mode == 'fast' else 8760
        print(f"Fetching {limit} hours of data...")

        df = fetch_data(limit=limit)
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

    elif args.command == 'best':
        try:
            import pandas as pd
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
