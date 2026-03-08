# AI Autonomous Iteration Guide

## Quick Start

**Single command to start AI:**
```
Hi, have a look at program.md and let's kick off a new experiment!
```

AI will run **forever** until you stop it.

## What Happens

1. AI reads `program.md` for instructions
2. Creates experiment branch
3. Loops infinitely:
   - Research factors (`research.py`)
   - Modify `strategy.py`
   - Run backtest
   - Keep if improved, discard if worse
   - Commit and repeat

## Files

| File | Role | Can AI Edit? |
|------|------|--------------|
| `program.md` | AI instructions | No (you edit) |
| `strategy.py` | Strategy code | Yes (AI edits) |
| `factors.py` | Factor library | No (read-only) |
| `research.py` | Research tools | No (read-only) |
| `prepare.py` | Backtest engine | No (read-only) |
| `results.tsv` | Experiment log | Yes (AI appends) |

## Key Commands AI Uses

```bash
# Research
python research.py --mode fast              # Find best factors
python research.py --multi-market           # Validate across markets
python research.py --optimize MA            # Grid search parameters

# Testing
python prepare.py run --mode fast           # Quick backtest (30s)
python prepare.py validate --mode fast      # Walk-forward validation
./test_all.sh                               # Complete test suite

# Git workflow
git commit -m "description"                 # Save experiment
git reset --hard HEAD~1                     # Discard if worse
```

## Monitoring

```bash
# Watch live progress
tail -f results.tsv

# View best score
sort -t$'\t' -k2 -rn results.tsv | head -1
```

## Stopping

Press `Ctrl+C` in Claude Code or send:
```
Stop now.
```

## Customization

Edit `program.md` to change AI behavior:

```markdown
## Research directions

Focus on:
1. Volatility-based strategies
2. Multi-timeframe analysis
3. Adaptive position sizing

**Constraints**:
- Minimum 20 trades
- Maximum 15% drawdown
```

AI will follow your instructions.

## Expected Performance

- **Speed**: 30 seconds/iteration
- **Overnight (8h)**: ~960 experiments
- **Goal**: Score > 0.8

## Example Session

```
User: Hi, have a look at program.md and let's kick off a new experiment!

AI: Creating branch autoquant/mar9...
AI: Running tests... ✓
AI: Baseline score: 0.524

AI: [Iteration 1] Analyzing factors...
    RSI_14_65_35 has IC=0.079 (best)
    Deploying to strategy.py...
    Score: 0.608 → Improved! Keeping.

AI: [Iteration 2] Trying MA crossover...
    Score: 0.590 → Worse. Discarding.

AI: [Iteration 3] Optimizing RSI parameters...
    ...continues forever...
```

## Troubleshooting

**AI stuck?**
```bash
tail -50 run.log
./test_all.sh
```

**Want to restart from best?**
```bash
git log --oneline results.tsv
git reset --hard <best-commit-hash>
```

**Change exploration strategy?**
Edit `program.md` and AI will adapt.

---

**Pro tip**: Start AI before bed, wake up to 1000+ experiments!
