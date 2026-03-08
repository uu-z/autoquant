# AutoQuant - Autonomous Quantitative Strategy Research

![Inspired by autoresearch](https://img.shields.io/badge/inspired%20by-autoresearch-blue)

## Overview

Give an AI agent a quantitative trading setup and let it experiment autonomously. It modifies the strategy, runs backtests, checks if results improved, keeps or discards, and repeats. You wake up in the morning to a log of experiments and (hopefully) a better strategy.

## Key Features

- **Autonomous Research**: AI runs indefinitely, exploring factor combinations and parameters
- **Factor Library**: 20+ technical indicators (MA, RSI, MACD, Bollinger Bands, etc.)
- **IC Analysis**: Information Coefficient calculation for factor validation
- **Multi-Market Testing**: Validate strategies across BTC, ETH, BNB
- **Walk-Forward Validation**: Out-of-sample testing to prevent overfitting
- **Git-Based Tracking**: Every experiment is a commit, easy to review and rollback
- **Fixed Time Budget**: Fair comparison across all experiments (~30s fast, ~5min full)

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

# 2. Verify setup
python prepare.py run --mode fast      # Quick backtest (~30s)
python research.py --mode fast         # Factor analysis
```

If both commands complete successfully, your setup is ready for autonomous research mode.

## Running the agent

Simply spin up Claude Code (or any AI agent with tool use) in this repo, then prompt:

```
Hi, have a look at program.md and let's kick off a new experiment!
```

The `program.md` file contains complete instructions for the AI agent to:
1. Create an experiment branch
2. Initialize results tracking
3. Run the autonomous loop (research → edit → test → keep/discard → repeat)

The agent will run **indefinitely** until you manually stop it.

**📖 See [AI_ITERATION_GUIDE.md](AI_ITERATION_GUIDE.md) for detailed instructions**

### What the AI does

```
[Loop 1] Factor research
→ python research.py --mode fast
→ Found RSI_14_65_35 IC=0.079 (best)

[Loop 2] Deploy to strategy
→ Edit strategy.py: add RSI filter
→ git commit -m "add RSI filter"
→ python prepare.py run --mode fast
→ Score: 0.608 (improved ✓) → keep

[Loop 3] Try combination
→ Edit strategy.py: add MA crossover
→ git commit -m "add MA crossover"
→ python prepare.py run --mode fast
→ Score: 0.590 (worse ✗) → git reset --hard HEAD~1

...continues indefinitely...
```

## Project structure

```
prepare.py          — backtest engine + utilities (read-only)
factors.py          — factor library with IC calculation (read-only)
research.py         — factor analysis and optimization (read-only)
strategy.py         — AI modifies this (uses factors from library)
program.md          — AI instructions (human edits this)
requirements.txt    — dependencies
results.tsv         — experiment log (auto-generated)
```

**Documentation:**
- [AI_ITERATION_GUIDE.md](AI_ITERATION_GUIDE.md) - Complete guide for AI autonomous research
- [QUICKSTART.md](QUICKSTART.md) - Quick reference and troubleshooting
- [program.md](program.md) - AI agent instructions and workflow

## Design choices

- **Single file to modify.** The agent only touches `strategy.py`. This keeps the scope manageable and diffs reviewable.
- **Fixed time budget.** Backtests always run for ~30 seconds (fast) or ~5 minutes (full), regardless of strategy complexity. This makes experiments directly comparable.
- **Git-driven.** Each experiment is a commit. Improvements are kept, failures are reset. The git history is your experiment log.
- **Self-contained.** No external dependencies beyond pandas/numpy/ccxt. No complex configs. One metric, one file, one goal.
- **AI-driven loop.** Unlike traditional AutoML, the AI agent controls the entire loop using tools (Edit, Bash, Read). No Python loop code needed.

## Example workflow

```
AI: Creating branch autoquant/mar8
AI: Running tests... ✓
AI: Baseline score: 0.524

AI: [Iteration 1] Analyzing factors...
    → python research.py --mode fast
    → RSI_14_65_35 has IC=0.079 (best)
    → Deploying to strategy.py...
    → git commit -m "add RSI filter"
    → python prepare.py run --mode fast
    → Score: 0.608 (improved from 0.524) ✓
    → Keeping commit

AI: [Iteration 2] Trying dynamic position sizing...
    → Edit strategy.py
    → git commit -m "dynamic position sizing"
    → python prepare.py run --mode fast
    → Score: 0.590 (worse than 0.608) ✗
    → git reset --hard HEAD~1

AI: [Iteration 3] Optimizing RSI parameters...
    → python research.py --optimize RSI --mode fast
    → Found optimal RSI(12, 70, 30)
    → Deploying and testing...
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

## FAQ

**Q: How long should I let the AI run?**
A: Overnight (8 hours) typically yields 500-1000 experiments. Longer runs may find better strategies but with diminishing returns.

**Q: What if the score keeps getting worse?**
A: The AI automatically discards bad experiments via `git reset`. Check `results.tsv` to find the best commit and reset to it.

**Q: Can I guide the AI's research direction?**
A: Yes! Edit `program.md` to add constraints, priorities, or specific research directions. The AI will follow your instructions.

**Q: How do I know if a strategy is overfitted?**
A: Run `python prepare.py validate --mode fast` for walk-forward validation. Also test on multiple markets with `python research.py --multi-market`.

**Q: What's a good composite score?**
A: Baseline is ~0.5-0.6. Good strategies score 0.7-0.8. Excellent strategies score >0.8. Scores >1.0 are rare and should be validated carefully.

**Q: Can I use this with other exchanges?**
A: Currently supports Binance. To add other exchanges, modify the data fetching logic in `prepare.py`.

## License

MIT
