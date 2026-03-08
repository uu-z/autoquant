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

Each experiment runs a backtest on crypto market data. The backtest runs for a **fixed time budget** (fast mode: ~30 seconds for 30 days data, full mode: ~5 minutes for 1 year data). You launch it simply as: `python prepare.py run --mode fast`.

**What you CAN do:**
- Modify `strategy.py` — this is the only file you edit. Everything is fair game: technical indicators, signal logic, position sizing, risk management.

**What you CANNOT do:**
- Modify `prepare.py`. It is read-only. It contains the fixed evaluation, data fetching, and backtest engine.
- Install new packages or add dependencies. You can only use pandas, numpy, and standard library.
- Modify the evaluation harness. The `calculate_score` function in `prepare.py` is the ground truth metric.

**The goal is simple: maximize the composite score** = sharpe_ratio * 0.5 - max_drawdown * 0.3 + win_rate * 0.2. Higher is better.

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
2. Modify `strategy.py` with an experimental idea by directly editing the code
3. git commit -m "descriptive message"
4. Run the experiment: `python prepare.py run --mode fast > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "Score:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv by appending a new line (use echo or Edit tool)
8. If score improved (higher), you "advance" the branch, keeping the git commit
9. If score is equal or worse, you git reset --hard HEAD~1 back to where you started

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Timeout**: Each experiment should take ~30 seconds (fast mode) or ~5 minutes (full mode). If a run exceeds 10 minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (syntax error, runtime error, etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, think harder — try combining strategies, adjust parameters, simplify code, read the existing strategy for inspiration. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each experiment takes you ~30 seconds then you can run approx 120/hour, for a total of about 1000 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!

## Research directions

Some ideas to explore (not exhaustive):

1. **Trend following**: MA crossover variations, MACD, Bollinger Bands, breakout strategies
2. **Mean reversion**: RSI, KDJ, overbought/oversold levels
3. **Momentum**: Price momentum, volume confirmation, rate of change
4. **Multi-factor**: Combine multiple signals with weights
5. **Risk management**: Dynamic position sizing, stop loss, trailing stop, volatility-based sizing
6. **Parameter tuning**: Adjust window sizes, thresholds, weights

## Constraints

- Single trade max position: 95%
- No future functions (no lookahead bias)
- Minimum trades > 10 (avoid overfitting)
- Keep code simple and readable
