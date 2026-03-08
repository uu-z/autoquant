"""
Research Workflow - Factor analysis and optimization

Usage:
    python research.py analyze --data btc  # Factor IC analysis
    python research.py optimize --factor MACrossover  # Parameter search
    python research.py ensemble  # Build factor portfolio
"""

import argparse
import pandas as pd
import numpy as np
from itertools import product
import importlib.util


def load_prepare():
    """Load prepare.py module"""
    spec = importlib.util.spec_from_file_location("prepare", "prepare.py")
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    return prepare


def load_factors():
    """Load factors.py module"""
    spec = importlib.util.spec_from_file_location("factors", "factors.py")
    factors_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(factors_module)
    return factors_module


class FactorAnalyzer:
    """Analyze factor quality"""

    def __init__(self, df):
        self.df = df

    def analyze_all(self):
        """Analyze all built-in factors"""
        factors_module = load_factors()

        # Test different parameter combinations
        candidates = [
            factors_module.MACrossover(10, 50),
            factors_module.MACrossover(15, 60),
            factors_module.MACrossover(20, 60),
            factors_module.MACrossover(25, 70),
            factors_module.RSIFilter(14, 70, 30),
            factors_module.RSIFilter(14, 65, 35),
            factors_module.RSIFilter(14, 60, 40),
            factors_module.MomentumFilter(3, 0.02),
            factors_module.MomentumFilter(5, 0.02),
            factors_module.MomentumFilter(10, 0.03),
            factors_module.BollingerBands(20),
            factors_module.BollingerBands(30),
            factors_module.VolatilityFilter(0.03),
        ]

        results = []
        for factor in candidates:
            ic = factor.ic(self.df, forward_periods=5)
            results.append({
                'factor': factor.name,
                'ic': ic,
                'abs_ic': abs(ic)
            })

        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('abs_ic', ascending=False)

        print("\n=== Factor IC Ranking ===")
        print(df_results.to_string(index=False))
        print(f"\nTop 3 factors:")
        for i, row in df_results.head(3).iterrows():
            print(f"  {row['factor']}: IC={row['ic']:.4f}")

        return df_results


class ParameterOptimizer:
    """Optimize factor parameters"""

    def __init__(self, df):
        self.df = df

    def grid_search_ma(self):
        """Grid search for MA crossover"""
        factors_module = load_factors()

        fast_range = [10, 15, 20, 25, 30]
        slow_range = [40, 50, 60, 70, 80]

        results = []
        for fast, slow in product(fast_range, slow_range):
            if fast >= slow:
                continue

            factor = factors_module.MACrossover(fast, slow)
            ic = factor.ic(self.df)
            results.append({
                'fast': fast,
                'slow': slow,
                'ic': ic,
                'abs_ic': abs(ic)
            })

        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('abs_ic', ascending=False)

        print("\n=== MA Parameter Grid Search ===")
        print(df_results.head(10).to_string(index=False))

        best = df_results.iloc[0]
        print(f"\nBest params: fast={int(best['fast'])}, slow={int(best['slow'])}, IC={best['ic']:.4f}")

        return df_results


class EnsembleBuilder:
    """Build factor ensemble"""

    def __init__(self, df):
        self.df = df

    def build_top_n(self, n=3):
        """Build ensemble from top N factors"""
        factors_module = load_factors()

        # Analyze factors
        analyzer = FactorAnalyzer(self.df)
        factor_ranking = analyzer.analyze_all()

        # Get top N
        top_factors = []
        for i, row in factor_ranking.head(n).iterrows():
            name = row['factor']

            # Parse factor name and create instance
            if name.startswith('MA_'):
                parts = name.split('_')
                fast, slow = int(parts[1]), int(parts[2])
                top_factors.append(factors_module.MACrossover(fast, slow))

            elif name.startswith('RSI_'):
                parts = name.split('_')
                window, upper, lower = int(parts[1]), int(parts[2]), int(parts[3])
                top_factors.append(factors_module.RSIFilter(window, upper, lower))

            elif name.startswith('Momentum_'):
                parts = name.split('_')
                window, threshold = int(parts[1]), float(parts[2])
                top_factors.append(factors_module.MomentumFilter(window, threshold))

            elif name.startswith('BB_'):
                parts = name.split('_')
                window = int(parts[1])
                top_factors.append(factors_module.BollingerBands(window))

        # Equal weight
        weights = [1.0 / len(top_factors)] * len(top_factors)
        combiner = factors_module.FactorCombiner(top_factors, weights)

        ensemble_ic = combiner.ic(self.df)

        print(f"\n=== Ensemble (Top {n}) ===")
        print(f"Factors: {[f.name for f in top_factors]}")
        print(f"Weights: {weights}")
        print(f"Ensemble IC: {ensemble_ic:.4f}")

        return combiner


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['analyze', 'optimize', 'ensemble'])
    parser.add_argument('--symbol', default='BTC/USDT')
    parser.add_argument('--mode', choices=['fast', 'full'], default='full')
    args = parser.parse_args()

    # Load data
    prepare = load_prepare()
    limit = 720 if args.mode == 'fast' else 8760
    print(f"Loading {limit} hours of {args.symbol} data...")
    df = prepare.fetch_data(symbol=args.symbol, limit=limit)

    if args.command == 'analyze':
        analyzer = FactorAnalyzer(df)
        analyzer.analyze_all()

    elif args.command == 'optimize':
        optimizer = ParameterOptimizer(df)
        optimizer.grid_search_ma()

    elif args.command == 'ensemble':
        builder = EnsembleBuilder(df)
        builder.build_top_n(n=3)
