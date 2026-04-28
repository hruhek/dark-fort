# Auto-Show Room Exits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically show room description and exit list whenever the player transitions back to EXPLORING phase, so they never need to press `M` manually.

**Architecture:** Add a `room_summary_messages()` helper to `GameEngine` that returns a room description line + exit lines. Call it from engine methods (`attack`, `flee`, `leave_shop`, `move_to_room`, `start_game`) at every point where the phase transitions to EXPLORING. The TUI needs no changes.

**Tech Stack:** Python, pytest, Textual (unchanged TUI layer)

---

### Task 1: Add `room_summary_messages()` helper + failing test

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add a new test class `TestRoomSummary` to `tests/game/test_engine.py`:

```python
class TestRoomSummary:
    def test_room_summary_describes_current_room(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        summary = engine.room_summary_messages()
        assert any(current.shape.lower() in m.lower() for m in summary)

    def test_room_summary_includes_exit_lines(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        summary = engine.room_summary_messages()
        for exit in current.exits:
            assert any(exit.direction.capitalize() in m for m in summary)

    def test_room_summary_entrance_has_exit_dungeon(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert current.id == 0
        summary = engine.room_summary_messages()
        assert any("Exit Dungeon" in m for m in summary)

    def test_room_summary_shows_explored_status(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        summary = engine.room_summary_messages()
        assert any("Explored" in m for m in summary)

    def test_room_summary_no_current_room_returns_empty(self):
        engine = GameEngine()
        assert engine.room_summary_messages() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestRoomSummary -v`
Expected: FAIL — `AttributeError: 'GameEngine' object has no attribute 'room_summary_messages'`

- [ ] **Step 3: Write minimal implementation**

Add `room_summary_messages` to `GameEngine` in `src/dark_fort/game/engine.py`:

```python
def room_summary_messages(self) -> list[str]:
    """Return room description + exit lines for the current room."""
    if not self.state.current_room:
        return []
    room = self.state.current_room
    status = "Explored" if room.explored else "Unexplored"
    messages = [f"You are in a {room.shape.lower()} room — {status}"]
    messages.extend(self.get_room_exits())
    return messages
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestRoomSummary -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: add room_summary_messages() helper to GameEngine"
```

---

### Task 2: Auto-append summary after combat kill + failing tests

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/game/test_engine.py`:

```python
class TestAutoShowRoomSummary:
    def test_attack_kill_shows_room_summary(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        engine.move_to_room(next_id)
        assert engine.state.phase == Phase.COMBAT
        # Kill the monster by dealing lethal damage with a high hit roll
        engine.state.combat.monster_hp = 1
        result = engine.attack(player_roll=6)
        assert result.phase == Phase.EXPLORING
        assert any("You are in a" in m for m in result.messages)

    def test_attack_no_summary_mid_combat(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        engine.move_to_room(next_id)
        assert engine.state.phase == Phase.COMBAT
        # Low roll — miss, combat continues
        result = engine.attack(player_roll=1)
        assert result.phase is None or result.phase == Phase.COMBAT
        assert not any("You are in a" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary -v`
Expected: FAIL — `test_attack_kill_shows_room_summary` fails because room summary is not appended to attack result messages.

- [ ] **Step 3: Implement — append summary after combat kill in `attack()`**

In `src/dark_fort/game/engine.py`, modify the `attack` method. After the block that sets `Phase.EXPLORING` on monster kill (around line 187-189), append the room summary:

```python
def attack(self, player_roll: int | None = None) -> ActionResult:
    if not self.state.combat:
        return ActionResult(messages=["No monster to attack."])

    result = resolve_combat_hit(self.state.player, self.state.combat, player_roll)

    if result.phase == Phase.GAME_OVER:
        self.state.phase = Phase.GAME_OVER
    elif result.phase == Phase.EXPLORING:
        self.state.combat = None
        if self.state.current_room:
            self.state.current_room.explored = True
        self.state.phase = Phase.EXPLORING

        result.messages.extend(self.room_summary_messages())

        if check_level_up(self.state):
            self.state.level_up_queue = True
            result.messages.append("You feel power coursing through you! Level up!")

    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: auto-append room summary after combat kill"
```

---

### Task 3: Auto-append summary after flee + failing tests

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing tests**

Add to `TestAutoShowRoomSummary` in `tests/game/test_engine.py`:

```python
    def test_flee_shows_room_summary(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        engine.move_to_room(next_id)
        if engine.state.phase != Phase.COMBAT:
            return
        result = engine.flee(player_roll=1)
        assert result.phase == Phase.EXPLORING
        assert any("You are in a" in m for m in result.messages)

    def test_flee_no_summary_on_death(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.hp = 1
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        engine.move_to_room(next_id)
        assert engine.state.phase == Phase.COMBAT
        result = engine.flee(player_roll=4)
        assert result.phase == Phase.GAME_OVER
        assert not any("You are in a" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_flee_shows_room_summary -v`
Expected: FAIL — flee result does not include room summary.

- [ ] **Step 3: Implement — append summary after survive-flee in `flee()`**

In `src/dark_fort/game/engine.py`, modify the `flee` method:

```python
def flee(self, player_roll: int | None = None) -> ActionResult:
    if not self.state.combat:
        return ActionResult(messages=["No monster to flee from."])

    result = flee_combat(self.state.player, player_roll)
    self.state.combat = None
    self.state.phase = result.phase or Phase.EXPLORING
    if self.state.phase == Phase.EXPLORING:
        result.messages.extend(self.room_summary_messages())
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_flee_shows_room_summary tests/game/test_engine.py::TestAutoShowRoomSummary::test_flee_no_summary_on_death -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: auto-append room summary after flee"
```

---

### Task 4: Auto-append summary after leaving shop + failing test

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `TestAutoShowRoomSummary` in `tests/game/test_engine.py`:

```python
    def test_leave_shop_shows_room_summary(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.phase = Phase.SHOP
        result = engine.leave_shop()
        assert any("You are in a" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_leave_shop_shows_room_summary -v`
Expected: FAIL — leave_shop result does not include room summary.

- [ ] **Step 3: Implement — append summary in `leave_shop()`**

In `src/dark_fort/game/engine.py`, modify `leave_shop`:

```python
def leave_shop(self) -> ActionResult:
    self.state.phase = Phase.EXPLORING
    self.state.shop_wares = []
    if self.state.current_room:
        self.state.current_room.explored = True
    messages = ["You leave the Void Peddler."]
    messages.extend(self.room_summary_messages())
    return ActionResult(messages=messages, phase=Phase.EXPLORING)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_leave_shop_shows_room_summary -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: auto-append room summary after leaving shop"
```

---

### Task 5: Auto-append summary in `move_to_room` for explored rooms + failing test

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `TestAutoShowRoomSummary` in `tests/game/test_engine.py`:

```python
    def test_move_to_explored_room_shows_summary(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        # Move to an adjacent room (triggers an event)
        engine.move_to_room(next_id)
        current = engine.state.current_room
        assert current is not None
        # Find the exit back to entrance
        back_exit = None
        for exit in current.exits:
            if exit.destination == 0:
                back_exit = exit
                break
        if back_exit is None:
            return
        # Mark current room as explored to make return easy
        current.explored = True
        engine.state.phase = Phase.EXPLORING
        engine.state.combat = None
        result = engine.move_to_room(back_exit.destination)
        assert any("You are in a" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_move_to_explored_room_shows_summary -v`
Expected: FAIL — re-entering an explored room currently doesn't include the "You are in a" header line.

- [ ] **Step 3: Implement — change header in `move_to_room()`**

In `src/dark_fort/game/engine.py`, modify `move_to_room`. The current code has `"You enter a {room.shape.lower()} room."` as a single message, followed by exit lines. Replace the separate message + exit calls with `room_summary_messages()` where appropriate:

```python
def move_to_room(self, room_id: int) -> ActionResult:
    room = self.state.rooms.get(room_id)
    if not room:
        return ActionResult(messages=["That exit leads nowhere."])

    self.state.current_room = room

    if not room.explored and room.result == "pending":
        room_result_idx = roll("d6") - 1
        room_result = ROOM_RESULTS[room_result_idx]

        result = resolve_room_event(room_result, self.state.player)

        if result.combat:
            self.state.combat = result.combat

        messages = [f"You enter a {room.shape.lower()} room."]

        if result.combat:
            messages.extend(result.messages)
            self.state.phase = Phase.COMBAT
            return ActionResult(messages=messages, phase=Phase.COMBAT)

        if result.phase == Phase.SHOP:
            self.state.shop_wares = list(SHOP_ITEMS)
            messages.extend(result.messages)
            self.state.phase = Phase.SHOP
            return ActionResult(messages=messages, phase=Phase.SHOP)

        messages.extend(result.messages)

        if result.explored:
            room.explored = True
        if result.silver_delta:
            self.state.player.silver += result.silver_delta
        if result.hp_delta:
            self.state.player.hp += result.hp_delta

        final_phase = result.phase or Phase.EXPLORING
        self.state.phase = final_phase

        if result.phase == Phase.GAME_OVER:
            return ActionResult(messages=messages, phase=Phase.GAME_OVER)

        messages.extend(self.room_summary_messages())
        return ActionResult(messages=messages, phase=self.state.phase)
    else:
        room.explored = True
        return ActionResult(
            messages=self.room_summary_messages(), phase=Phase.EXPLORING
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_move_to_explored_room_shows_summary -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/game/test_engine.py -v`
Expected: All tests pass (no regressions).

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: auto-append room summary in move_to_room for all paths"
```

---

### Task 6: Add room description header to `start_game()` + failing test

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `TestAutoShowRoomSummary` in `tests/game/test_engine.py`:

```python
    def test_start_game_includes_room_description_header(self):
        engine = GameEngine()
        result = engine.start_game()
        entrance = engine.state.current_room
        assert entrance is not None
        assert any(entrance.shape.lower() in m.lower() for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_start_game_includes_room_description_header -v`
Expected: MAY PASS already — `start_game()` already calls `get_room_exits()`. The test checks for the room shape in messages, which the current `"You enter the Dark Fort..."` message doesn't include. If it passes, we still want the header line. Let's check for a specific "You are in a" header:

```python
    def test_start_game_includes_room_description_header(self):
        engine = GameEngine()
        result = engine.start_game()
        assert any("You are in a" in m for m in result.messages)
```

- [ ] **Step 3: Implement — add header to `start_game()`**

In `src/dark_fort/game/engine.py`, modify `start_game`. Replace the separate `get_room_exits()` call with `room_summary_messages()`:

Change this:
```python
        # Show exits before encounter so player knows their options
        if self.state.current_room:
            exit_info = self.get_room_exits()
            messages.extend(exit_info)
```

To this:
```python
        if self.state.current_room:
            messages.extend(self.room_summary_messages())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_start_game_includes_room_description_header -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `make test`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: use room_summary_messages in start_game for consistent header"
```

---

### Task 7: Edge case — no room summary on GAME_OVER from room events + test

**Files:**
- Modify: `src/dark_fort/game/engine.py` (already handled in Task 5 refactor)
- Test: `tests/game/test_engine.py`

The Task 5 refactor of `move_to_room` already returns early for `Phase.GAME_OVER` without appending the summary. Let's verify with a test.

- [ ] **Step 1: Write the test**

Add to `TestAutoShowRoomSummary` in `tests/game/test_engine.py`:

```python
    def test_move_to_room_game_over_no_summary(self):
        from unittest.mock import patch
        from dark_fort.game.models import RoomEventResult

        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination

        with patch(
            "dark_fort.game.engine.resolve_room_event",
            return_value=RoomEventResult(
                messages=["A pit trap! You fall to your death!"],
                phase=Phase.GAME_OVER,
                hp_delta=-999,
            ),
        ):
            result = engine.move_to_room(next_id)

        assert not any("You are in a" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestAutoShowRoomSummary::test_move_to_room_game_over_no_summary -v`
Expected: PASS (already handled by refactor)

- [ ] **Step 3: Commit**

```bash
git add tests/game/test_engine.py
git commit -m "test: verify no room summary on GAME_OVER from room events"
```

---

### Task 8: Run full lint + typecheck + test suite

**Files:** None (verification only)

- [ ] **Step 1: Run lint**

Run: `make lint`
Expected: All checks pass.

- [ ] **Step 2: Run tests**

Run: `make test`
Expected: All tests pass.

- [ ] **Step 3: Move backlog item to done**

Edit `docs/backlog.md`: remove the "wandering the dungeon" section.
Edit `docs/backlog_done.md`: add it as completed.