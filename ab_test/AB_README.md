# OpenCode A/B test toolkit

Run controlled A/B comparisons between OpenCode setups using the `OPENCODE_CONFIG` environment variable — no config swapping, no backups.

## Files

| File | Purpose |
|---|---|
| `glm.json` | GLM-5.1 plan + build, Kimi K2.6 general, Qwen3.6 explore |
| `deepseek.json` | DeepSeek V4 Pro plan, V4 Flash build, Kimi K2.6 general, Qwen3.6 explore |
| `test-prompt.md` | The verbatim prompt and standard responses guide |
| `ab.sh` | Single runner — resets project, launches OpenCode with variant config |

## How it works

OpenCode reads config from `OPENCODE_CONFIG` env var when set, instead of `~/.config/opencode/opencode.json`. So:

```bash
OPENCODE_CONFIG=./glm.json opencode
```

…runs OpenCode with the GLM config without touching your global config. Your normal setup is untouched between and after test runs.

## Quick start

```bash
chmod +x ab.sh

# From project directory:
~/path/to/opencode-ab-test/ab.sh glm
# or
~/path/to/opencode-ab-test/ab.sh deepseek

# From anywhere, specify project:
~/path/to/opencode-ab-test/ab.sh glm ~/Developer/dark-fort
```

The script:
1. Prints the test prompt for you to copy
2. Launches OpenCode with the variant config

When OpenCode exits, you're back to your normal environment — nothing to restore.

## Manual usage (no script)

If you prefer:

```bash
# Run with GLM
OPENCODE_CONFIG=~/path/to/glm.json opencode

# Run with DeepSeek
OPENCODE_CONFIG=~/path/to/deepseek.json opencode
```

## Even simpler: shell aliases

Add to `~/.zshrc`:

```bash
alias oc-glm='OPENCODE_CONFIG=~/path/to/opencode-ab-test/glm.json opencode'
alias oc-deepseek='OPENCODE_CONFIG=~/path/to/opencode-ab-test/deepseek.json opencode'
```

Then just `oc-glm` or `oc-deepseek` from any project.

## Comparing fairly

- Pick a different backlog task for each run (don't repeat the same task — second run benefits from your accumulated context)
- Use the standard responses in `test-prompt.md` verbatim
- Don't add corrective reminders mid-session
- Note both session IDs from `~/.local/share/opencode/sessions/`
