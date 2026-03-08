# strategy.py - AI implements strategy logic here

def compute_factors(df):
    """Calculate technical indicators and custom factors

    Args:
        df: OHLCV dataframe (columns: open, high, low, close, volume, timestamp)

    Returns:
        df: Dataframe with added factor columns
    """
    # Simple moving averages
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_60'] = df['close'].rolling(60).mean()
    return df

def generate_signals(df):
    """Generate trading signals

    Returns:
        df: Dataframe with 'signal' column (1=buy, -1=sell, 0=hold)
    """
    df['signal'] = 0
    df.loc[df['sma_20'] > df['sma_60'], 'signal'] = 1
    df.loc[df['sma_20'] < df['sma_60'], 'signal'] = -1
    return df

def position_sizing(df, capital):
    """Position sizing and risk management

    Returns:
        df: Dataframe with 'position_size' column (0-1 range, 1=full position)
    """
    df['position_size'] = 0.95  # Default 95% position
    return df
