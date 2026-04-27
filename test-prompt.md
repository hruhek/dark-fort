# A/B test prompt

Paste this into OpenCode after launching with one of the variant configs.

```
Pick the top unchecked task from docs/backlog.md and take it through the full Superpowers workflow to a finished PR.

I expect you to:
- Use the brainstorming skill to clarify requirements before any design
- Get my approval on the design before writing the implementation plan
- Use subagent-driven-development with strict TDD: failing test first, minimal code to pass, refactor
- Cover positive paths AND negative/edge cases (errors, terminal states like GAME_OVER, invalid input)
- Use finishing-a-development-branch to open the PR

Follow AGENTS.md without me prompting. If you need Build mode, ask me to switch — don't work around permissions. Keep the tasklist visible via todowrite.

Start by loading the brainstorming skill and reading docs/backlog.md.
```

## Standard responses to use during the run

Same in both runs:

| Situation | Response |
|---|---|
| Brainstorming clarifying questions | Answer factually and concisely. Same answers in both runs. |
| Multiple options offered | "go with option 1" |
| Design awaiting approval | "design approved" |
| Plan awaiting approval | "plan approved, proceed" |
| Mode switch requested | "switched to build mode" |
| Mid-implementation status | "continue" |
| Implementation complete | "open the PR" |

## Don't

- Add reminders ("don't forget TDD", "what about the branch?")
- Help with edge cases — let the model decide
- Switch modes preemptively — wait for the agent to ask
