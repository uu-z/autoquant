# autoquant

This is an autonomous quantitative strategy research system.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar8`). The branch `autoquant/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoquant/<tag>` from current main.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `README.md` — repository context
   - `prepare.py` — fixed constants, data fetching, backtest engine, evaluation. Do not modify.
   - `strategy.py` — the file you modify. Technical indicators, signal logic, position sizing.
4. **Initialize results.tsv**: Create `results.tsv` with header row and baseline entry. The baseline results are already known from running once (score: ~0.524). Do NOT re-run the baseline — just record it.
5. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment runs a backtest on crypto market data. The backtest runs for a **fixed time budget** (fast mode: ~30 seconds for 30 days data, full mode: ~5 minutes for 1 year data).

**Commands**:
- `python prepare.py run --mode fast` - Quick backtest (30 days)
- `python prepare.py run --mode fast --symbol ETH/USDT` - Test on different pair
- `python prepare.py validate --mode fast` - Walk-forward validation (防过拟合)

**What you CAN do:**
- Modify `strategy.py` — the Strategy class with full control:
  - `self.params` - All strategy parameters
  - `compute_factors()` - Use 50+ precomputed indicators or create custom
  - `generate_signals()` - Any signal logic
  - `position_sizing()` - Dynamic sizing with access to current state
  - `on_trade()` - Adaptive logic based on trade results
  - `self.state` - Store any internal state for adaptive strategies

**Available precomputed indicators** (in prepare.py):
- Moving averages: sma_{5,10,15,20,25,30,50,60,100,200}, ema_{same}
- RSI: rsi_{7,10,14,21}
- MACD: macd, macd_signal, macd_hist
- Bollinger Bands: bb_mid_{20,30}, bb_upper_{20,30}, bb_lower_{20,30}
- Volatility: atr_14
- Volume: volume_sma_20, volume_ratio
- Momentum: momentum_{3,5,10,20}
- Stochastic: stoch_k, stoch_d

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only.
- Install new packages. Use pandas, numpy, standard library only.
- Modify the evaluation harness.

**The goal**: Maximize composite score = sharpe_ratio * 0.5 - max_drawdown * 0.3 + win_rate * 0.2

**Realistic trading costs** (now included):
- Binance fees: 0.02% maker, 0.04% taker
- Slippage: 0.05% base + market impact (larger orders = more slippage)
- This makes the problem harder but results more realistic

**Anti-overfitting**:
- Use `validate` command periodically to check robustness
- Test on multiple symbols (BTC/USDT, ETH/USDT, SOL/USDT)
- Prefer simpler strategies that generalize better

**Simplicity criterion**: All else being equal, simpler is better. A small improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the improvement magnitude. A 0.001 score improvement that adds 20 lines of hacky code? Probably not worth it. A 0.001 improvement from deleting code? Definitely keep. An improvement of ~0 but much simpler code? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the backtest as is.

## Output format

Once the script finishes it prints a summary like this:

```
Results:
  Sharpe Ratio: 0.930
  Max Drawdown: 0.071
  Win Rate: 0.400
  Total Return: 2.14%
  Trades: 10
  Score: 0.524
```

You can extract the key metric from the output:

```bash
python prepare.py run --mode fast | grep "Score:"
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 5 columns:

```
commit	score	memory_gb	status	description
```

1. git commit hash (short, 7 chars)
2. composite score achieved (e.g. 0.524567) — use 0.000000 for crashes
3. peak memory in GB (use 0.0 for now, placeholder)
4. status: `keep`, `discard`, or `crash`
5. short text description of what this experiment tried

Example:

```
commit	score	memory_gb	status	description
a1b2c3d	0.524000	0.0	keep	baseline MA crossover
b2c3d4e	0.608000	0.0	keep	add RSI filter
c3d4e5f	0.510000	0.0	discard	switch to EMA (worse)
d4e5f6g	0.000000	0.0	crash	invalid signal logic
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoquant/mar8`).

LOOP FOREVER:

1. Look at the git state: the current branch/commit we're on
2. Modify `strategy.py` (the Strategy class) with an experimental idea
3. git commit -m "descriptive message"
4. Run the experiment: `python prepare.py run --mode fast > run.log 2>&1`
5. Read out the results: `grep "Score:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to debug.
7. Record the results in results.tsv
8. If score improved (higher), keep the commit
9. If score is equal or worse, `git reset --hard HEAD~1` to revert

**Every 10 experiments**: Run validation to check robustness
```bash
python prepare.py validate --mode fast > validate.log 2>&1
grep "Score:" validate.log
```
If validation score is much lower than training score (>20% drop), the strategy is overfitting.

**Every 20 experiments**: Test on different symbol
```bash
python prepare.py run --mode fast --symbol ETH/USDT > eth.log 2>&1
```
Good strategies should work across multiple pairs.

**Smart iteration** (every 10 experiments):
1. Read results.tsv
2. Identify what types of changes worked (e.g., "MA window tuning", "RSI filters")
3. Generate 3 variations of successful patterns
4. Test those first before random exploration

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Timeout**: Each experiment should take ~30 seconds (fast mode) or ~5 minutes (full mode). If a run exceeds 10 minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (syntax error, runtime error, etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — try combining strategies, adjust parameters, simplify code, read the existing strategy for inspiration. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~30 seconds then you can run approx 120/hour, for a total of about 1000 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!

## Research directions

Professional quant strategies to explore:

1. **Trend following**: MA crossover, MACD, Donchian channels, breakout
2. **Mean reversion**: RSI extremes, Bollinger Band bounces, Z-score
3. **Momentum**: Price momentum + volume confirmation, rate of change
4. **Multi-factor**: Combine trend + momentum + volatility with weights
5. **Adaptive strategies**: Adjust parameters based on market regime (use `self.state` and `on_trade()`)
6. **Risk management**:
   - Volatility-based sizing (use atr_14)
   - Kelly criterion
   - Drawdown-based reduction
   - Win/loss streak adaptation
7. **Market microstructure**: Volume profile, bid-ask spread proxies
8. **Regime detection**: Trending vs ranging markets, adjust strategy accordingly

**Advanced ideas**:
- **Ensemble**: Combine multiple uncorrelated signals
- **Machine learning**: Use historical features to predict next-bar return
- **Statistical arbitrage**: Mean reversion on spread between correlated pairs
- **Volatility trading**: Long volatility in low-vol regimes, short in high-vol

## Constraints

- Single trade max position: 95%
- No future functions (no lookahead bias)
- Minimum trades > 10 (avoid overfitting)
- Keep code simple and readable
