# AutoQuant - Autonomous Quantitative Strategy Research

![Inspired by autoresearch](https://img.shields.io/badge/inspired%20by-autoresearch-blue)

## Overview

Give an AI agent a quantitative trading setup and let it experiment autonomously. It modifies the strategy, runs backtests, checks if results improved, keeps or discards, and repeats. You wake up in the morning to a log of experiments and (hopefully) a better strategy.

## How it works

The repo has three core files:

- **`prepare.py`** — fixed constants, data fetching (Binance), backtest engine, and evaluation. Not modified by AI.
- **`strategy.py`** — the single file the agent edits. Contains technical indicators, signal logic, and position sizing. **This file is edited and iterated on by the agent**.
- **`program.md`** — instructions for the AI agent. Point your agent here and let it go. **This file is edited and iterated on by the human**.

By design, backtests run for a **fixed time budget** (~30 seconds for fast mode, ~5 minutes for full mode). The metric is **composite score** = sharpe*0.5 - drawdown*0.3 + winrate*0.2 — higher is better.

## Quick start

**Requirements:** Python 3.10+, internet connection (for Binance API)

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run complete test suite (one command)
./test_all.sh
```

The test script will:
- ✅ Run 9 unit tests
- ✅ Execute 30-day backtest
- ✅ Perform factor IC analysis

If all tests pass, your setup is ready for autonomous research mode.

### Manual testing (optional)

```bash
# Run individual components
python prepare.py run --mode fast      # Quick backtest
python research.py --mode fast         # Factor analysis
pytest -v                              # Unit tests only
```

## Running the agent

Simply spin up Claude Code (or any AI agent with tool use) in this repo, then prompt:

```
Hi have a look at program.md and let's kick off a new experiment! let's do the setup first.
```

The `program.md` file contains complete instructions for the AI agent to:
1. Create an experiment branch
2. Initialize results tracking
3. Run the autonomous loop (edit → commit → test → keep/discard → repeat)

The agent will run **indefinitely** until you manually stop it.

## Project structure

```
prepare.py      — backtest engine + utilities (do not modify)
strategy.py     — AI modifies this (factors, signals, position sizing)
program.md      — AI instructions (human edits this)
requirements.txt — dependencies
results.tsv     — experiment log (auto-generated)
```

## Design choices

- **Single file to modify.** The agent only touches `strategy.py`. This keeps the scope manageable and diffs reviewable.
- **Fixed time budget.** Backtests always run for ~30 seconds (fast) or ~5 minutes (full), regardless of strategy complexity. This makes experiments directly comparable.
- **Git-driven.** Each experiment is a commit. Improvements are kept, failures are reset. The git history is your experiment log.
- **Self-contained.** No external dependencies beyond pandas/numpy/ccxt. No complex configs. One metric, one file, one goal.
- **AI-driven loop.** Unlike traditional AutoML, the AI agent controls the entire loop using tools (Edit, Bash, Read). No Python loop code needed.

## Example workflow

```
AI: Creating branch autoquant/mar8
AI: Initializing results.tsv with baseline
AI: [Iteration 1] Trying RSI filter...
    → Edit strategy.py
    → git commit -m "add RSI filter"
    → python prepare.py run --mode fast > run.log 2>&1
    → Score: 0.608 (improved from 0.524)
    → Keeping commit ✓
AI: [Iteration 2] Trying dynamic position sizing...
    → Edit strategy.py
    → git commit -m "dynamic position sizing"
    → python prepare.py run --mode fast > run.log 2>&1
    → Score: 0.590 (worse than 0.608)
    → git reset --hard HEAD~1 ✗
AI: [Iteration 3] Trying MACD crossover...
    ...continues indefinitely...
```

## Comparison with autoresearch

| Aspect | autoresearch | autoquant |
|--------|-------------|-----------|
| Domain | LLM training | Quant trading |
| Metric | val_bpb (lower better) | composite score (higher better) |
| Time budget | 5 min fixed | 30s (fast) or 5min (full) |
| Data source | HuggingFace dataset | Binance API |
| Modified file | train.py | strategy.py |

Both use the same AI-driven autonomous loop pattern.

## License

MIT
