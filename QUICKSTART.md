# 🚀 Quick Start Guide

## Launch AI Agent

In Claude Code:
```
Hi, have a look at program.md and let's kick off a new experiment!
```

AI will automatically:
1. Create experiment branch `autoquant/<date>`
2. Run tests to verify environment
3. Initialize results.tsv
4. **Loop forever**: research → modify → test → keep/discard

## What AI Does

```
[Loop 1] Factor research
→ python research.py --mode fast
→ Found RSI_14_65_35 IC=0.079 (best)

[Loop 2] Deploy to strategy
→ Edit strategy.py: self.factor = RSIFilter(14, 65, 35)
→ git commit -m "use RSI filter"
→ python prepare.py run --mode fast
→ Score: 0.608 (improved ✓) → keep

[Loop 3] Try factor combination
→ Edit strategy.py: add MACrossover
→ git commit -m "add MA crossover"
→ python prepare.py run --mode fast
→ Score: 0.590 (worse ✗) → git reset --hard HEAD~1

[Loop 4] Parameter optimization
→ python research.py --optimize MA --mode fast
→ Found optimal MA(15, 60)
→ Deploy and test...

...continues forever until you stop it
```

## Monitor Progress

```bash
# Watch experiment log
tail -f results.tsv

# View current score
git log --oneline | head -5

# View best results
sort -t$'\t' -k2 -rn results.tsv | head -5

# Check last backtest output
tail -50 run.log
```

**Results format:**
```
timestamp         score   description
2026-03-08_18:00  0.608   add RSI filter
2026-03-08_18:01  0.590   add MA crossover (discarded)
2026-03-08_18:02  0.625   optimize RSI params
```

## Stop AI

In Claude Code, press `Ctrl+C` or send:
```
Stop the experiment loop now.
```

## Expected Results

- **Speed**: ~30 seconds per iteration (fast mode)
- **8-hour run**: ~960 experiments
- **Goal**: Find strategy with composite score > 0.8
- **Baseline**: Initial score typically ~0.5-0.6

## Key Files

- `program.md` - AI instructions (you can edit)
- `strategy.py` - AI modifies this file
- `results.tsv` - Experiment log
- `factors.py` - Factor library (read-only)
- `research.py` - Research tools (read-only)

## Advanced Usage

### Customize AI Behavior

Edit `program.md` "Research directions" section:

```markdown
## Research directions

Priority exploration:
1. Volatility breakout strategies
2. Multi-timeframe confirmation
3. Dynamic stop-loss
```

### Set Constraints

Add to `program.md`:

```markdown
**Additional constraints**:
- Minimum trades > 20
- Maximum drawdown < 15%
- Must have positive returns on all 3 markets
```

AI will follow these rules.

## Troubleshooting

### AI stuck
```bash
# Check last run
tail -50 run.log

# Test manually
python prepare.py run --mode fast
python research.py --mode fast
```

### Score keeps dropping
```bash
# Return to best commit
git log --oneline results.tsv
git reset --hard <best-commit>

# Let AI continue from here
```

### Want more aggressive exploration
Add to `program.md`:
```markdown
**Exploration strategy**: Try completely different approach every 5 iterations
```

---

**Remember**: AI runs indefinitely until you stop it. Perfect for overnight runs!
