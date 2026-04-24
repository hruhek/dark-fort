# AGENTS.md

## Rules

- **NEVER** change `docs/DARK_FORT.md` — canonical game design document.
- **ALWAYS** run `make test` and `make lint` before committing.
- **ALWAYS** open a new branch when starting work on a new task.
- **ALWAYS** pick the next open item from the top of `docs/backlog.md`.
- **ALWAYS** move completed items to `docs/backlog_done.md`.
- **ALWAYS** use TDD for new features and bug fixes — write failing test first, then make it pass.

## Commands

```
make help     # list all targets
make test     # run pytest
make lint     # ruff check + format + ty check
```

Use `uv run <cmd>` for any direct command.

## Architecture

- `src/dark_fort/game/` — pure domain logic, zero Textual deps
- `src/dark_fort/tui/` — thin Textual layer, renders game state
- `game/` returns `ActionResult` Pydantic models; TUI calls engine methods and displays results

## Key files

- `game/engine.py` — `GameEngine` owns `GameState`, exposes all game actions
- `game/rules.py` — combat, flee, leveling, traps, scroll effects
- `game/tables.py` — all DARK_FORT reference tables as typed data
- `tui/screens.py` — TitleScreen, GameScreen, ShopScreen, GameOverScreen
- `tui/widgets.py` — StatusBar, LogView, CommandBar

## Testing

- `game/` tests: pure pytest, no Textual
- `tui/` tests: `DarkFortApp().run_test()` for async integration tests
- `asyncio_mode = "auto"` in pyproject.toml

## Ty suppressions

- `# ty: ignore[invalid-return-type]` on `game_app` properties (Textual's `self.app` returns `App[Unknown]`)
- `# ty: ignore[unresolved-attribute]` in test files for `pilot.app.engine`

