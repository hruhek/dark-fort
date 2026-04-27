# Wandering the Dungeon

## Summary

Polish the existing room-to-room navigation in DARK FORT: add an explicit
"select exit" mode to the TUI (guarding against accidental digit-key moves),
and cover all `move_to_room` paths with tests. The underlying engine logic is
already correct — the work is in test coverage and UX guard-rails.

## Changes

### Engine (`src/dark_fort/game/engine.py`)

No engine logic changes. `move_to_room` already handles:
- Phase transitions (COMBAT, SHOP, GAME_OVER, EXPLORING)
- Explored flag, silver/HP deltas
- Valid/invalid room IDs

### TUI (`src/dark_fort/tui/screens.py`)

Add a `selecting_exit: reactive[bool] = reactive(False)` flag on `GameScreen`,
mirroring the existing `selecting_item` pattern:

| Event | Behavior |
|---|---|
| MOVE key/button | Set `selecting_exit = True`, show exits, prompt "Pick a door or Esc" |
| Digit key when `selecting_exit` | Move to that exit's destination |
| Digit key when NOT `selecting_exit` | Ignored |
| Invalid exit digit | Error message, stay in selection mode |
| Escape | Cancel selection, return to exploring |
| Phase change after move | `selecting_exit = False` (handled by `_handle_phase_change`) |

### Tests

**Engine (pure pytest, `tests/game/test_engine.py`):**
- `move_to_room` invalid ID → error message
- `move_to_room` already explored room
- `move_to_room` that triggers SHOP → phase = SHOP
- `move_to_room` resulting in GAME_OVER (pit trap death)
- `get_room_exits` output format (directions, explored labels)

**TUI (Textual async, `tests/tui/test_flows.py`):**
- Press M → selection mode on, exits shown
- Valid digit during select → moves to room, exits shown for new room
- Invalid digit → error, stays in selection
- Escape → cancels selection
- Digit *without* M → no move, no error

### Edge Cases

- Room event resolves to GAME_OVER during `move_to_room` → phase = GAME_OVER,
  GameOverScreen shown
- Room with no exits → empty exit list, can't move further
- Entrance room always shows "0. Exit Dungeon"
- Selection mode cleared on any phase change
- Bad exit number keeps selection active (retry allowed)
