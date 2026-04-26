# Wandering the Dungeon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show room exits to the player after combat ends, flee resolves, and leaving the Void Peddler shop.

**Architecture:** Add `get_room_exits()` output to the `ActionResult.messages` of 3 engine methods (`attack`, `flee`, `leave_shop`) when they transition back to EXPLORING phase. No TUI changes needed — the existing `_log_messages(result.messages)` in `GameScreen` handles all display.

**Tech Stack:** Python 3.12+, Pydantic, Textual, pytest

---

## File Structure

- Modify: `src/dark_fort/game/engine.py` — 3 methods, ~3 lines added total
- Modify: `tests/tui/test_screens.py` — 3 new integration tests

---

### Task 1: Show exits after killing a monster (attack)

**Files:**
- Modify: `src/dark_fort/game/engine.py:183-196`
- Test: `tests/tui/test_screens.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_screens.py`, inside `TestGameScreenActions`:

```python
async def test_exits_displayed_after_killing_monster(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        # Set up a monster with minimal HP so one attack kills it
        monster = Monster(
            name="Blood-Drenched Skeleton",
            tier=MonsterTier.WEAK,
            points=3,
            damage="d4",
            hp=1,
        )
        pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=1)
        pilot.app.engine.state.phase = Phase.COMBAT
        await pilot.pause()
        pilot.app.screen._update_commands()
        await pilot.pause()
        # Kill the monster
        await pilot.press("a")
        await pilot.pause()
        log = pilot.app.screen.query_one("#log")
        # After combat, exits should appear in the log
        messages = [
            log.lines[i].text
            for i in range(log.message_count - 5, log.message_count)
        ]
        assert any("→" in m for m in messages), f"Expected exit info in log messages: {messages}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_killing_monster -v
```
Expected: FAIL — exits not shown after combat

- [ ] **Step 3: Implement exits after attack**

In `src/dark_fort/game/engine.py`, in the `attack()` method, after the existing block (around line ~194-196):

```python
            if check_level_up(self.state):
                self.state.level_up_queue = True
                result.messages.append("You feel power coursing through you! Level up!")

        # Show exits when returning to exploring after combat
        if result.phase == Phase.EXPLORING:
            exit_info = self.get_room_exits()
            result.messages.extend(exit_info)
```

Insert after the `check_level_up` block, before `return result`.

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_killing_monster -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/tui/test_screens.py
git commit -m "feat: show room exits after killing a monster"
```

---

### Task 2: Show exits after fleeing (flee)

**Files:**
- Modify: `src/dark_fort/game/engine.py:198-206`
- Test: `tests/tui/test_screens.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_screens.py`, inside `TestGameScreenActions`:

```python
async def test_exits_displayed_after_flee(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        initial_hp = pilot.app.engine.state.player.hp
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)
        pilot.app.engine.state.phase = Phase.COMBAT
        await pilot.pause()
        pilot.app.screen._update_commands()
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        log = pilot.app.screen.query_one("#log")
        messages = [
            log.lines[i].text
            for i in range(log.message_count - 5, log.message_count)
        ]
        assert any("→" in m for m in messages), f"Expected exit info in log messages: {messages}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_flee -v
```
Expected: FAIL — exits not shown after flee

- [ ] **Step 3: Implement exits after flee**

In `src/dark_fort/game/engine.py`, in the `flee()` method, after the existing block (around line ~205):

```python
        self.state.combat = None
        self.state.phase = result.phase or Phase.EXPLORING

        # Show exits when returning to exploring after fleeing
        if self.state.phase == Phase.EXPLORING:
            exit_info = self.get_room_exits()
            result.messages.extend(exit_info)

        return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_flee -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/tui/test_screens.py
git commit -m "feat: show room exits after fleeing"
```

---

### Task 3: Show exits after leaving the shop (leave_shop)

**Files:**
- Modify: `src/dark_fort/game/engine.py:267-275`
- Test: `tests/tui/test_screens.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/tui/test_screens.py`, inside `TestGameScreenActions`:

```python
async def test_exits_displayed_after_leaving_shop(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        pilot.app.engine.state.phase = Phase.SHOP
        pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)
        await pilot.pause()
        pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))
        await pilot.pause()
        await pilot.press("l")
        await pilot.pause()
        assert pilot.app.screen.__class__.__name__ == "GameScreen"
        log = pilot.app.screen.query_one("#log")
        messages = [
            log.lines[i].text
            for i in range(log.message_count - 5, log.message_count)
        ]
        assert any("→" in m for m in messages), f"Expected exit info in log messages: {messages}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_leaving_shop -v
```
Expected: FAIL — exits not shown after leaving shop

- [ ] **Step 3: Implement exits after leave_shop**

In `src/dark_fort/game/engine.py`, replace the `leave_shop()` method body:

Current code:
```python
    def leave_shop(self) -> ActionResult:
        self.state.phase = Phase.EXPLORING
        self.state.shop_wares = []
        if self.state.current_room:
            self.state.current_room.explored = True
        return ActionResult(
            messages=["You leave the Void Peddler."], phase=Phase.EXPLORING
        )
```

Replace with:
```python
    def leave_shop(self) -> ActionResult:
        self.state.phase = Phase.EXPLORING
        self.state.shop_wares = []
        if self.state.current_room:
            self.state.current_room.explored = True
        messages = ["You leave the Void Peddler."]
        messages.extend(self.get_room_exits())
        return ActionResult(messages=messages, phase=Phase.EXPLORING)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/tui/test_screens.py::TestGameScreenActions::test_exits_displayed_after_leaving_shop -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/tui/test_screens.py
git commit -m "feat: show room exits after leaving shop"
```

---

### Self-Review

- [ ] Run full test suite to verify nothing broke:

```bash
uv run make test
```
Expected: All tests pass

- [ ] Run lint:

```bash
uv run make lint
```
Expected: No errors

- [ ] Verify backlog.md item is checked and noted
