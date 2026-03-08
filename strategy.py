# strategy.py - Factor-based strategy

from factors import MomentumFilter
import numpy as np
import pandas as pd
from typing import Dict, Any


class Strategy:
    """
    Factor-based strategy using IC-validated factors.

    Based on research.py analysis:
    - Top factors: RSI(14,65,35), Momentum(10,0.03), MA(15,60)
    - Ensemble IC: ~0.15 (better than individual)
    """

    def __init__(self) -> None:
        # Single factor strategy (multi-market validated)
        self.factor = MomentumFilter(5, 0.015)

        # Risk management state
        self.state = {
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'total_trades': 0,
        }

        # Parameters
        self.params = {
            'position_base': 0.95,
            'reduce_after_losses': 3,
            'increase_after_wins': 3,
        }

    def initialize(self, df: pd.DataFrame, initial_capital: float) -> None:
        """Called once before backtest"""
        pass

    def compute_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute factor signals.
        All indicators are precomputed in prepare.py
        """
        # Factors compute their own signals
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals using factor.

        Returns:
            df with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        df['signal'] = self.factor.compute(df)
        return df

    def position_sizing(self, df: pd.DataFrame, capital: float, current_position: float, context: Dict[str, Any]) -> float:
        """
        Dynamic position sizing based on volatility (ATR).

        Args:
            df: Historical data up to current bar
            capital: Available capital
            current_position: Current position size
            context: Dict with 'trades' and 'equity' history

        Returns:
            float: Position size (0-1 range)
        """
        base_size = self.params['position_base']

        # Volatility-based sizing
        if 'atr_14' in df.columns and len(df) > 0:
            current_atr = df['atr_14'].iloc[-1]
            current_price = df['close'].iloc[-1]

            # Check if ATR is valid (not NaN)
            if not np.isnan(current_atr) and current_atr > 0:
                current_vol = current_atr / current_price

                # Target volatility: 3% (typical crypto)
                target_vol = 0.03
                vol_adjustment = target_vol / max(current_vol, 0.01)  # Avoid division by zero
                vol_adjustment = np.clip(vol_adjustment, 0.5, 1.5)  # Limit adjustment

                size = base_size * vol_adjustment
            else:
                # ATR not ready yet, use base size
                size = base_size
        else:
            size = base_size

        # Reduce after consecutive losses
        if self.state['consecutive_losses'] >= self.params['reduce_after_losses']:
            size *= 0.5

        # Increase after consecutive wins (cautiously)
        if self.state['consecutive_wins'] >= self.params['increase_after_wins']:
            size = min(0.95, size * 1.1)

        return np.clip(size, 0.1, 0.95)

    def on_trade(self, trade: Dict[str, Any], df: pd.DataFrame) -> None:
        """
        Update state after each trade.

        Args:
            trade: Dict with trade info
            df: Historical data up to current bar
        """
        self.state['total_trades'] += 1

        # Track win/loss streaks (simplified)
        if trade['type'] == 'sell':
            # Estimate PnL from price change
            if len(df) > 1:
                entry_price = df['close'].iloc[-2]
                exit_price = trade['price']

                if exit_price > entry_price:
                    self.state['consecutive_wins'] += 1
                    self.state['consecutive_losses'] = 0
                else:
                    self.state['consecutive_losses'] += 1
                    self.state['consecutive_wins'] = 0
