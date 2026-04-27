# Wandering the Dungeon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish room-to-room navigation with TUI guard mode and full test coverage for `move_to_room`.

**Architecture:** Engine logic is correct as-is. Add a `selecting_exit` reactive flag on `GameScreen` (mirrors `selecting_item`). Digit keys only trigger movement during selection mode. Comprehensive engine + TUI tests cover all paths.

**Tech Stack:** Python, Textual, pytest, Pydantic

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/game/test_engine.py` | Modify (add tests) | Engine-level move_to_room / get_room_exits tests |
| `src/dark_fort/tui/screens.py` | Modify | Add selecting_exit on GameScreen, guard digit keys |
| `tests/tui/test_flows.py` | Modify | TUI integration tests for wandering flow |

---

### Task 1: Engine tests for move_to_room edge cases

**Files:**
- Modify: `tests/game/test_engine.py` (add to existing `TestGameEngine` class)
- Read: `src/dark_fort/game/engine.py` (for reference)
- Read: `src/dark_fort/game/rules.py` (for reference)

- [ ] **Step 1: Write failing test for move_to_room with invalid room ID**

```python
# Add to TestGameEngine in tests/game/test_engine.py

def test_move_to_room_invalid_id_returns_error(self):
    engine = GameEngine()
    engine.start_game()
    result = engine.move_to_room(9999)
    assert engine.state.current_room is not None
    assert "leads nowhere" in " ".join(result.messages).lower()
```

- [ ] **Step 2: Run test to verify it fails (or passes if already implemented)**

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_move_to_room_invalid_id_returns_error -v`

- [ ] **Step 3: If the test fails, fix the engine** (currently `move_to_room` returns error for bad ID, should already pass)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_move_to_room_invalid_id_returns_error -v`

- [ ] **Step 5: Write failing test for move_to_room to already-explored room**

```python
def test_move_to_room_already_explored(self):
    engine = GameEngine()
    engine.start_game()
    current = engine.state.current_room
    assert current is not None
    assert len(current.exits) > 0
    next_id = current.exits[0].destination
    next_room = engine.state.rooms[next_id]
    # Mark as explored before moving
    next_room.explored = True
    result = engine.move_to_room(next_id)
    # Should still be explored after move
    assert next_room.explored is True
    assert engine.state.current_room is not None
    assert engine.state.current_room.id == next_id
```

- [ ] **Step 6: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_move_to_room_already_explored -v`

- [ ] **Step 7: Write failing test for move_to_room that triggers GAME_OVER**

This tests the pit trap death path. We mock `resolve_room_event` to return a GAME_OVER result.

```python
from unittest.mock import patch
from dark_fort.game.models import RoomEventResult

def test_move_to_room_game_over_from_trap(self):
    engine = GameEngine()
    engine.start_game()
    current = engine.state.current_room
    assert current is not None
    assert len(current.exits) > 0
    next_id = current.exits[0].destination
    next_room = engine.state.rooms[next_id]
    next_room.result = "pending"
    with patch("dark_fort.game.engine.resolve_room_event") as mock:
        mock.return_value = RoomEventResult(
            messages=["You fall in and take 6 damage!", "You have fallen!"],
            phase=Phase.GAME_OVER,
        )
        result = engine.move_to_room(next_id)
    assert engine.state.phase == Phase.GAME_OVER
    assert any("fallen" in m.lower() for m in result.messages)
```

- [ ] **Step 8: Run test to verify it passes** (should pass since engine already handles phase from result)

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_move_to_room_game_over_from_trap -v`

- [ ] **Step 9: Write failing test for move_to_room that triggers SHOP**

```python
def test_move_to_room_triggers_shop(self):
    engine = GameEngine()
    engine.start_game()
    current = engine.state.current_room
    assert current is not None
    assert len(current.exits) > 0
    next_id = current.exits[0].destination
    next_room = engine.state.rooms[next_id]
    next_room.result = "pending"
    with patch("dark_fort.game.engine.resolve_room_event") as mock:
        from dark_fort.game.enums import Phase, RoomEvent
        mock.return_value = RoomEventResult(
            messages=["You encounter the Void Peddler."],
            phase=Phase.SHOP,
        )
        result = engine.move_to_room(next_id)
    assert engine.state.phase == Phase.SHOP
    assert any("void peddler" in m.lower() for m in result.messages)
```

- [ ] **Step 10: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_move_to_room_triggers_shop -v`

- [ ] **Step 11: Write failing test for get_room_exits output**

```python
def test_get_room_exits_shows_explored_status(self):
    engine = GameEngine()
    engine.start_game()
    current = engine.state.current_room
    assert current is not None
    exit_lines = engine.get_room_exits()
    assert len(exit_lines) > 0
    for line in exit_lines:
        assert "Explored" in line or "Unexplored" in line
        # Each line should have a door number
        assert any(c.isdigit() for c in line.split(".")[0])
    # Entrance room should show exit 0
    if current.id == 0:
        assert any("0." in line for line in exit_lines)
```

- [ ] **Step 12: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestGameEngine::test_get_room_exits_shows_explored_status -v`

- [ ] **Step 13: Commit**

```bash
git add tests/game/test_engine.py
git commit -m "test: add move_to_room edge case tests"
```

---

### Task 2: Add selecting_exit mode to GameScreen

**Files:**
- Modify: `src/dark_fort/tui/screens.py`
- Read: `src/dark_fort/tui/widgets.py` (for reference, no changes)
- Read: `src/dark_fort/game/phase_states.py` (for reference, no changes)

- [ ] **Step 1: Write the failing TUI test for selecting_exit mode**

```python
# Add to tests/tui/test_flows.py

class TestWanderingFlow:
    async def test_wandering_move_to_exit(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            # Press M to activate exit selection
            await pilot.press("m")
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            # Pick first exit number (door 1)
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.phase != Phase.GAME_OVER
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tui/test_flows.py::TestWanderingFlow::test_wandering_move_to_exit -v`

- [ ] **Step 3: Add selecting_exit flag and guard digit keys in GameScreen**

Add the reactive flag to `GameScreen`:

```python
class GameScreen(Screen):
    selecting_exit: reactive[bool] = reactive(False)
```

Modify `on_key` method — around line 107, the exit selection block should change from:

```python
# Handle exit selection in exploring phase
if (
    self.engine.state.phase == Phase.EXPLORING
    and event.character
    and event.character.isdigit()
):
```

To:

```python
# Handle exit selection in exploring phase (only in selection mode)
if (
    self.engine.state.phase == Phase.EXPLORING
    and self.selecting_exit
    and event.character
    and event.character.isdigit()
):
```

Then modify `on_button_pressed` to handle MOVE by activating selection mode — around line 159, the `_handle_command` block for MOVE should set selection mode. Change the `on_button_pressed` method to check for `Command.MOVE`:

After the line `command = Command(action)`, add a check for MOVE:

```python
if command == Command.MOVE:
    self.selecting_exit = True
    exit_info = self.engine.get_room_exits()
    self._log_messages(exit_info)
    self._log_messages(["Pick a door number (or Esc to cancel)"])
    return
```

Also modify `on_key` for keyboard M — around line 118, where keyboard shortcuts are handled, add before the `_handle_command` call:

```python
if command == Command.MOVE:
    self.selecting_exit = True
    exit_info = self.engine.get_room_exits()
    self._log_messages(exit_info)
    self._log_messages(["Pick a door number (or Esc to cancel)"])
    return
```

Then modify the `_handle_phase_change` method to reset selection:

```python
def _handle_phase_change(self, result: ActionResult) -> None:
    self.selecting_item = False
    self.selecting_exit = False
    ...
```

Add Escape key handling for exit selection — in `on_key`, add before the `selecting_item` block:

```python
# Handle exit selection mode (digit keys or Escape)
if self.selecting_exit:
    if event.key == "escape":
        self.selecting_exit = False
        self._log_messages(["Cancelled."])
        self._update_commands()
        return
    if event.character and event.character.isdigit():
        digit = int(event.character)
        current = self.engine.state.current_room
        if current:
            if digit == 0 and current.id == 0:
                result = self.engine.exit_dungeon()
                self._log_messages(result.messages)
                return
            for exit in current.exits:
                if exit.door_number == digit:
                    result = self.engine.move_to_room(exit.destination)
                    self._log_messages(result.messages)
                    if result.phase:
                        self._handle_phase_change(result)
                    self._update_commands()
                    self._refresh_status()
                    return
            self._log_messages([f"No exit number {digit}."])
    return
```

Also modify the `on_key` to pull the `selecting_item` escape handling up. The full key handler structure should be:

```
1. Handle selecting_exit mode (digit → move, Escape → cancel)
2. Handle selecting_item mode (digit → use item, Escape → cancel)
3. Handle keyboard shortcuts (letter keys)
```

Remove the old exit-selection digit handling from the shortcuts section.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_flows.py::TestWanderingFlow::test_wandering_move_to_exit -v`

- [ ] **Step 5: Write failing test for Escape cancels exit selection**

```python
    async def test_escape_cancels_exit_selection(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("m")
            await pilot.pause()
            # Verify selection mode is active
            assert pilot.app.screen.selecting_exit is True  # ty: ignore[unresolved-attribute]
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.screen.selecting_exit is False  # ty: ignore[unresolved-attribute]
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_flows.py::TestWanderingFlow::test_escape_cancels_exit_selection -v`

- [ ] **Step 7: Write failing test for digit without M does nothing**

```python
    async def test_digit_without_move_mode_does_nothing(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_room = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            assert pilot.app.screen.selecting_exit is False  # ty: ignore[unresolved-attribute]
            await pilot.press("1")
            await pilot.pause()
            # Should NOT have moved
            assert pilot.app.engine.state.current_room.id == initial_room  # ty: ignore[unresolved-attribute]
```

- [ ] **Step 8: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_flows.py::TestWanderingFlow::test_digit_without_move_mode_does_nothing -v`

- [ ] **Step 9: Write failing test for invalid exit number**

```python
    async def test_invalid_exit_number_shows_error(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("m")
            await pilot.pause()
            # Press a high digit that doesn't match any exit
            await pilot.press("9")
            await pilot.pause()
            # Should stay in selection mode and show error
            assert pilot.app.screen.selecting_exit is True  # ty: ignore[unresolved-attribute]
```

- [ ] **Step 10: Run test to verify it passes**

Run: `uv run pytest tests/tui/test_flows.py::TestWanderingFlow::test_invalid_exit_number_shows_error -v`

- [ ] **Step 11: Run the full test suite to verify nothing is broken**

Run: `uv run make test && uv run make lint`

- [ ] **Step 12: Commit**

```bash
git add src/dark_fort/tui/screens.py tests/tui/test_flows.py
git commit -m "feat: add exit selection mode for dungeon wandering"
```
