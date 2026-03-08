"""
Research Workflow - Factor IC analysis and parameter optimization

Usage:
    python research.py  # Analyze all factors, show top 5
    python research.py --multi-market  # Test on BTC/ETH/SOL
    python research.py --optimize MA  # Grid search MA params
"""

import argparse
import pandas as pd
import numpy as np
from itertools import product
from typing import Optional, Dict
from prepare import fetch_data
from factors import (
    MACrossover, RSIFilter, MomentumFilter,
    BollingerBands, VolatilityFilter
)


def analyze_factors(df: pd.DataFrame, multi_market_dfs: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
    """
    Compute IC for all factor candidates.

    Returns: DataFrame sorted by |IC|
    """
    # Test parameter combinations
    candidates = [
        MACrossover(10, 50), MACrossover(15, 60), MACrossover(20, 60),
        RSIFilter(14, 70, 30), RSIFilter(14, 65, 35), RSIFilter(14, 60, 40),
        MomentumFilter(3, 0.02), MomentumFilter(5, 0.02), MomentumFilter(10, 0.03),
        BollingerBands(20), BollingerBands(30),
        VolatilityFilter(0.03),
    ]

    results = []
    for factor in candidates:
        if multi_market_dfs:
            # Multi-market IC
            ics = {sym: factor.ic(df_sym, forward_periods=5)
                   for sym, df_sym in multi_market_dfs.items()}
            avg_ic = np.mean(list(ics.values()))
            all_positive = all(ic > 0 for ic in ics.values())

            results.append({
                'factor': factor.name,
                'ic': avg_ic,
                'abs_ic': abs(avg_ic),
                'all_positive': all_positive,
                **{f'ic_{sym}': ic for sym, ic in ics.items()}
            })
        else:
            # Single market IC
            ic = factor.ic(df, forward_periods=5)
            results.append({
                'factor': factor.name,
                'ic': ic,
                'abs_ic': abs(ic)
            })

    df_results = pd.DataFrame(results)

    if multi_market_dfs:
        df_results = df_results[df_results['all_positive']]  # Filter

    df_results = df_results.sort_values('abs_ic', ascending=False)

    print("\n=== Factor IC Ranking ===")
    print(df_results.head(10).to_string(index=False))

    return df_results


def optimize_ma(df: pd.DataFrame) -> pd.DataFrame:
    """Grid search for MA crossover parameters"""
    fast_range = [10, 15, 20, 25, 30]
    slow_range = [40, 50, 60, 70, 80]

    results = []
    for fast, slow in product(fast_range, slow_range):
        if fast >= slow:
            continue

        factor = MACrossover(fast, slow)
        ic = factor.ic(df)
        results.append({'fast': fast, 'slow': slow, 'ic': ic, 'abs_ic': abs(ic)})

    df_results = pd.DataFrame(results).sort_values('abs_ic', ascending=False)

    print("\n=== MA Parameter Grid Search ===")
    print(df_results.head(10).to_string(index=False))

    best = df_results.iloc[0]
    print(f"\nBest: MA({int(best['fast'])}, {int(best['slow'])}), IC={best['ic']:.4f}")

    return df_results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='BTC/USDT')
    parser.add_argument('--mode', choices=['fast', 'full'], default='full')
    parser.add_argument('--multi-market', action='store_true')
    parser.add_argument('--optimize', choices=['MA'], help='Run parameter optimization')
    args = parser.parse_args()

    # Load data
    limit = 720 if args.mode == 'fast' else 8760

    if args.multi_market:
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        multi_market_dfs = {}
        for sym in symbols:
            print(f"Loading {limit}h {sym}...")
            multi_market_dfs[sym] = fetch_data(symbol=sym, limit=limit)
        df = multi_market_dfs['BTC/USDT']
        analyze_factors(df, multi_market_dfs)
    else:
        print(f"Loading {limit}h {args.symbol}...")
        df = fetch_data(symbol=args.symbol, limit=limit)

        if args.optimize == 'MA':
            optimize_ma(df)
        else:
            analyze_factors(df)
