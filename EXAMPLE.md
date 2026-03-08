# Example: How to Use AutoQuant

## Starting a New Experiment

### Step 1: Initial Prompt

```
You: Hi have a look at program.md and let's kick off a new experiment!
     let's do the setup first.
```

### Step 2: AI Setup

AI will:
1. Read program.md
2. Propose a run tag (e.g., "mar8")
3. Create branch `autoquant/mar8`
4. Initialize results.tsv with baseline

### Step 3: Autonomous Loop

AI enters infinite loop:

```python
while True:
    # 1. Think of improvement idea
    idea = "Add RSI filter to reduce false signals"

    # 2. Edit strategy.py
    Edit(file_path="strategy.py", ...)

    # 3. Commit
    Bash(command="git add strategy.py && git commit -m 'add RSI filter'")

    # 4. Run backtest
    Bash(command="python prepare.py run --mode fast > run.log 2>&1")

    # 5. Read results
    result = Bash(command="grep 'Score:' run.log")
    score = parse_score(result)

    # 6. Decide
    if score > best_score:
        # Keep commit
        log_to_tsv(commit, score, "keep", idea)
        best_score = score
    else:
        # Rollback
        Bash(command="git reset --hard HEAD~1")
        log_to_tsv(commit, score, "discard", idea)

    # 7. Continue (never stops)
```

## Example Conversation

```
You: Hi have a look at program.md and let's kick off a new experiment!

AI: I'll set up a new autoquant experiment. Let me read program.md first...
    [reads program.md]

    I propose run tag "mar8" based on today's date. The branch autoquant/mar8
    will be created. Is this okay?

You: yes

AI: Creating experiment branch...
    [Bash: git checkout -b autoquant/mar8]

    Initializing results.tsv...
    [Write: results.tsv with header]

    Recording baseline (score: 0.524)...
    [Edit: append baseline to results.tsv]

    Setup complete! Starting autonomous loop...

    === Iteration 1 ===
    Idea: Add RSI indicator to filter overbought/oversold conditions

    [Edit: strategy.py - add RSI calculation]
    [Bash: git commit -m "add RSI filter"]
    [Bash: python prepare.py run --mode fast > run.log 2>&1]
    [Bash: grep "Score:" run.log]

    Result: Score: 0.608
    Previous best: 0.524
    Improvement: +0.084 ✓

    Keeping commit 1a2b3c4
    [Edit: append to results.tsv]

    === Iteration 2 ===
    Idea: Adjust RSI thresholds (30/70 → 25/75)

    [Edit: strategy.py - change thresholds]
    [Bash: git commit -m "adjust RSI thresholds"]
    [Bash: python prepare.py run --mode fast > run.log 2>&1]
    [Bash: grep "Score:" run.log]

    Result: Score: 0.595
    Previous best: 0.608
    Worse: -0.013 ✗

    Rolling back...
    [Bash: git reset --hard HEAD~1]
    [Edit: append to results.tsv]

    === Iteration 3 ===
    Idea: Add volume confirmation to signals

    [continues indefinitely...]

You: [after 8 hours] stop

AI: Stopping autonomous loop.

    Summary:
    - Total iterations: 987
    - Improvements kept: 23
    - Best score: 0.742 (commit 9f8e7d6)
    - Description: "RSI + volume + dynamic position sizing"

    You can view full results in results.tsv and git log.
```

## Monitoring Progress

While AI is running, you can monitor in another terminal:

```bash
# Watch results file
watch -n 5 'tail -10 results.tsv'

# Watch git commits
watch -n 5 'git log --oneline -10'

# Check current score
tail -1 results.tsv | cut -f2
```

## Stopping and Resuming

### Stop
Just interrupt the AI (Ctrl+C or stop in UI)

### Resume
```
You: Continue the experiment from where we left off

AI: Resuming autoquant/mar8...
    [Bash: git checkout autoquant/mar8]
    [Read: results.tsv to get best score]

    Current best: 0.742 (commit 9f8e7d6)
    Continuing autonomous loop...

    === Iteration 988 ===
    ...
```

## Tips

1. **Let it run overnight**: ~1000 experiments in 8 hours
2. **Check in morning**: Review results.tsv and git log
3. **Fast mode for exploration**: Use `--mode fast` (30s each)
4. **Full mode for validation**: Switch to `--mode full` (5min each) for final tests
5. **Trust the AI**: It will try many ideas, most will fail, that's normal
