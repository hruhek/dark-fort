# Wandering Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After any transition from a non-EXPLORING phase back to EXPLORING, automatically re-display room exits so the player can seamlessly choose their next door.

**Architecture:** Append `self.get_room_exits()` to ActionResult messages in three engine methods (`attack`, `flee`, `leave_shop`) when they transition back to EXPLORING. This matches the existing pattern in `start_game()` and `move_to_room()`. No TUI or model changes needed.

**Tech Stack:** Python, pytest, Pydantic

---

### Task 1: TDD — attack shows exits after combat kill

**Files:**
- Modify: `src/dark_fort/game/engine.py:186-196`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add a new test class `TestWanderingLoop` to `tests/game/test_engine.py`:

```python
class TestWanderingLoop:
    def test_attack_shows_exits_after_combat_kill(self):
        from dark_fort.game.enums import MonsterTier, Phase
        from dark_fort.game.models import CombatState, Monster

        engine = GameEngine()
        engine.start_game()
        # Set up combat with a 1-HP monster so any hit kills it
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=1
        )
        engine.state.combat = CombatState(monster=monster, monster_hp=1)
        engine.state.phase = Phase.COMBAT

        result = engine.attack(player_roll=6)
        assert result.phase == Phase.EXPLORING
        assert any("→" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_attack_shows_exits_after_combat_kill -v`
Expected: FAIL — `assert any("→" in m for m in result.messages)` is False

- [ ] **Step 3: Write minimal implementation**

In `src/dark_fort/game/engine.py`, in the `attack` method, after the level-up check inside the `elif result.phase == Phase.EXPLORING:` block, add:

```python
        elif result.phase == Phase.EXPLORING:
            self.state.combat = None
            if self.state.current_room:
                self.state.current_room.explored = True
            self.state.phase = Phase.EXPLORING

            if check_level_up(self.state):
                self.state.level_up_queue = True
                result.messages.append("You feel power coursing through you! Level up!")

            result.messages.extend(self.get_room_exits())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_attack_shows_exits_after_combat_kill -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: show room exits after combat kill"
```

---

### Task 2: TDD — flee shows exits when player survives

**Files:**
- Modify: `src/dark_fort/game/engine.py:198-206`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `TestWanderingLoop` in `tests/game/test_engine.py`:

```python
    def test_flee_shows_exits_after_successful_flee(self):
        from dark_fort.game.enums import MonsterTier, Phase
        from dark_fort.game.models import CombatState, Monster

        engine = GameEngine()
        engine.start_game()
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        engine.state.combat = CombatState(monster=monster, monster_hp=5)
        engine.state.phase = Phase.COMBAT

        # Flee with roll=1 (1 d4 damage, player has 15+ HP, survives)
        result = engine.flee(player_roll=1)
        assert result.phase == Phase.EXPLORING
        assert any("→" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_flee_shows_exits_after_successful_flee -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

In `src/dark_fort/game/engine.py`, in the `flee` method, add exit display after setting phase:

```python
    def flee(self, player_roll: int | None = None) -> ActionResult:
        """Flee from combat."""
        if not self.state.combat:
            return ActionResult(messages=["No monster to flee from."])

        result = flee_combat(self.state.player, player_roll)
        self.state.combat = None
        self.state.phase = result.phase or Phase.EXPLORING
        if self.state.phase == Phase.EXPLORING:
            result.messages.extend(self.get_room_exits())
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_flee_shows_exits_after_successful_flee -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: show room exits after fleeing combat"
```

---

### Task 3: TDD — leave_shop shows exits

**Files:**
- Modify: `src/dark_fort/game/engine.py:267-275`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `TestWanderingLoop` in `tests/game/test_engine.py`:

```python
    def test_leave_shop_shows_exits(self):
        from dark_fort.game.enums import Phase

        engine = GameEngine()
        engine.start_game()
        # Enter a room, then set up shop state
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0

        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)

        result = engine.leave_shop()
        assert result.phase == Phase.EXPLORING
        assert any("→" in m for m in result.messages)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_leave_shop_shows_exits -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

In `src/dark_fort/game/engine.py`, modify `leave_shop`:

```python
    def leave_shop(self) -> ActionResult:
        """Leave the Void Peddler."""
        self.state.phase = Phase.EXPLORING
        self.state.shop_wares = []
        if self.state.current_room:
            self.state.current_room.explored = True
        messages = ["You leave the Void Peddler."]
        messages.extend(self.get_room_exits())
        return ActionResult(messages=messages, phase=Phase.EXPLORING)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop::test_leave_shop_shows_exits -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: show room exits after leaving shop"
```

---

### Task 4: GAME_OVER edge case tests — no exits on death

**Files:**
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write tests for both GAME_OVER paths**

Add to `TestWanderingLoop` in `tests/game/test_engine.py`:

```python
    def test_attack_no_exits_on_game_over(self):
        from unittest.mock import patch
        from dark_fort.game.enums import MonsterTier, Phase
        from dark_fort.game.models import ActionResult, CombatState, Monster

        engine = GameEngine()
        engine.start_game()
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        engine.state.combat = CombatState(monster=monster, monster_hp=5)
        engine.state.phase = Phase.COMBAT

        with patch(
            "dark_fort.game.engine.resolve_combat_hit",
            return_value=ActionResult(
                messages=["You have fallen!"], phase=Phase.GAME_OVER
            ),
        ):
            result = engine.attack()

        assert engine.state.phase == Phase.GAME_OVER
        assert not any("→" in m for m in result.messages)

    def test_flee_no_exits_on_game_over(self):
        from unittest.mock import patch
        from dark_fort.game.enums import MonsterTier, Phase
        from dark_fort.game.models import CombatState, Monster

        engine = GameEngine()
        engine.start_game()
        engine.state.player.hp = 1
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        engine.state.combat = CombatState(monster=monster, monster_hp=5)
        engine.state.phase = Phase.COMBAT

        # Fleeing with d4=15 would kill a player with 1 HP
        with patch("dark_fort.game.engine.flee_combat") as mock_flee:
            mock_flee.return_value = ActionResult(
                messages=["You flee!", "You have fallen!"], phase=Phase.GAME_OVER
            ):
            result = engine.flee()

        assert engine.state.phase == Phase.GAME_OVER
        assert not any("→" in m for m in result.messages)
```

- [ ] **Step 2: Run all wandering loop tests**

Run: `uv run pytest tests/game/test_engine.py::TestWanderingLoop -v`
Expected: All 5 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/game/test_engine.py
git commit -m "test: add GAME_OVER edge case tests for wandering loop"
```

---

### Task 5: Full verification + backlog update

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 2: Run lint and typecheck**

Run: `make lint`
Expected: All checks pass

- [ ] **Step 3: Update backlog**

Move "wandering the dungeon" from `docs/backlog.md` to `docs/backlog_done.md`.

- [ ] **Step 4: Final commit**

```bash
git add docs/backlog.md docs/backlog_done.md
git commit -m "docs: move wandering loop to backlog_done"
```