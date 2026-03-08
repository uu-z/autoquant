# strategy.py - Factor-based strategy

from factors import MACrossover, RSIFilter, MomentumFilter, FactorCombiner


class Strategy:
    """
    Factor-based strategy using IC-validated factors.

    Based on research.py analysis:
    - Top factors: RSI(14,65,35), Momentum(10,0.03), MA(15,60)
    - Ensemble IC: ~0.15 (better than individual)
    """

    def __init__(self):
        # Build factor ensemble (use only positive IC factors)
        self.factors = [
            RSIFilter(14, 65, 35),      # IC: 0.077 (positive)
            MACrossover(15, 60),        # IC: 0.064 (positive)
        ]

        # Weight by IC magnitude
        self.combiner = FactorCombiner(
            self.factors,
            weights=[0.55, 0.45],  # Proportional to IC
            method='vote'  # Use voting instead of weighted
        )

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

    def initialize(self, df, initial_capital):
        """Called once before backtest"""
        pass

    def compute_factors(self, df):
        """
        Compute factor signals.
        All indicators are precomputed in prepare.py
        """
        # Factors compute their own signals
        return df

    def generate_signals(self, df):
        """
        Generate trading signals using factor ensemble.

        Returns:
            df with 'signal' column: 1=buy, -1=sell, 0=hold
        """
        # Use factor combiner
        df['signal'] = self.combiner.compute(df)
        return df

    def position_sizing(self, df, capital, current_position, context):
        """
        Dynamic position sizing based on win/loss streaks.

        Args:
            df: Historical data up to current bar
            capital: Available capital
            current_position: Current position size
            context: Dict with 'trades' and 'equity' history

        Returns:
            float: Position size (0-1 range)
        """
        size = self.params['position_base']

        # Reduce after consecutive losses
        if self.state['consecutive_losses'] >= self.params['reduce_after_losses']:
            size *= 0.5

        # Increase after consecutive wins (cautiously)
        if self.state['consecutive_wins'] >= self.params['increase_after_wins']:
            size = min(0.95, size * 1.1)

        return size

    def on_trade(self, trade, df):
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
