# AutoQuant Quick Start

## Initial Setup

```bash
# 1. Clone/navigate to repo
cd autoquant

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Test single backtest
python prepare.py run --mode fast
```

Expected output:
```
Fetching 720 hours of data...

Results:
  Sharpe Ratio: 0.930
  Max Drawdown: 0.071
  Win Rate: 0.400
  Total Return: 2.14%
  Trades: 10
  Score: 0.524
```

## Running AI Autonomous Mode

### Start the AI agent

In Claude Code (or any AI agent with tool use), prompt:

```
Hi have a look at program.md and let's kick off a new experiment! let's do the setup first.
```

The AI will:
1. Ask you for a run tag (e.g., "mar8")
2. Create branch `autoquant/mar8`
3. Initialize `results.tsv`
4. Start the autonomous loop

### What the AI does

```
Loop forever:
  1. Edit strategy.py (add RSI, adjust MA, etc.)
  2. git commit -m "try RSI filter"
  3. python prepare.py run --mode fast > run.log 2>&1
  4. grep "Score:" run.log
  5. If improved: keep commit
     If worse: git reset --hard HEAD~1
  6. Append result to results.tsv
  7. Repeat (never stops until you interrupt)
```

### Monitor progress

```bash
# View experiment log
cat results.tsv

# View git history
git log --oneline

# View current strategy
cat strategy.py

# View best result
python prepare.py best
```

### Stop the AI

Simply interrupt the AI agent (Ctrl+C in terminal, or stop in UI).

## Example Session

```
You: Hi have a look at program.md and let's kick off a new experiment!

AI: I'll help you set up a new autoquant experiment. Let me propose a run tag
    based on today's date: "mar8". Is this okay?

You: yes

AI: Creating branch autoquant/mar8...
    [git checkout -b autoquant/mar8]

    Initializing results.tsv...
    [creates results.tsv with header and baseline]

    Setup complete! Starting autonomous loop...

    === Iteration 1 ===
    Idea: Add RSI filter to reduce false signals
    [edits strategy.py]
    [git commit -m "add RSI filter"]
    [runs backtest]
    Score: 0.608 (improved from 0.524) ✓
    Keeping commit.

    === Iteration 2 ===
    Idea: Try dynamic position sizing based on volatility
    [edits strategy.py]
    [git commit -m "dynamic position sizing"]
    [runs backtest]
    Score: 0.590 (worse than 0.608) ✗
    Rolling back.

    === Iteration 3 ===
    ...continues indefinitely...
```

## Troubleshooting

**Backtest fails:**
- Check internet connection (needs Binance API)
- Verify dependencies: `pip list | grep -E "ccxt|pandas|numpy"`
- Check Python version: `python --version` (need 3.10+)

**Git errors:**
- Ensure you're in a git repo: `git status`
- Check branch: `git branch`

**No improvements:**
- Let it run longer (100+ iterations)
- Check results.tsv for patterns
- Review strategy.py for bugs

## Tips

- **Fast iteration**: Use `--mode fast` (30s per experiment)
- **Final validation**: Use `--mode full` (5min, more reliable)
- **Let it run overnight**: ~1000 experiments in 8 hours (fast mode)
- **Review in morning**: Check results.tsv and git log
