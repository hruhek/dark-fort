# TUI Integration Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add comprehensive TUI integration tests covering focused screen interactions and end-to-end game flows.

**Architecture:** Two new test files using `DarkFortApp().run_test()` with async pilot. `test_screens.py` tests each screen's interactions in isolation. `test_flows.py` tests multi-screen game flows. Engine state is manipulated directly to avoid randomness.

**Tech Stack:** Python 3.13, pytest, pytest-asyncio (auto mode), Textual (run_test/pilot)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `tests/tui/test_screens.py` | Focused interaction tests per screen (TitleScreen, GameScreen, ShopScreen, GameOverScreen) |
| `tests/tui/test_flows.py` | End-to-end game flows (death, shop, flee, victory) |
| `tests/tui/test_widgets.py` | Existing file — leave unchanged |

No source files are modified. All changes are test-only.

---

### Task 1: TitleScreen and GameScreen Phase Tests

**Files:**
- Create: `tests/tui/test_screens.py` (first portion)

- [ ] **Step 1: Write TitleScreen and GameScreen phase tests**

```python
from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Command, MonsterTier, Phase
from dark_fort.game.models import CombatState, Monster, Player, Weapon
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import GameOverScreen, GameScreen, ShopScreen, TitleScreen
from dark_fort.tui.widgets import CommandBar, StatusBar


class TestTitleScreen:
    async def test_pressing_enter_starts_game(self):
        async with DarkFortApp().run_test() as pilot:
            assert pilot.app.screen.__class__.__name__ == "TitleScreen"
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0

    async def test_starting_game_sets_exploring_phase(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING


class TestGameScreenPhaseCommands:
    async def test_exploring_phase_shows_explore_and_inventory(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.EXPLORE in cmd_bar.commands
            assert Command.INVENTORY in cmd_bar.commands

    async def test_combat_phase_shows_attack_flee_use_item(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)
            pilot.app.engine.state.phase = Phase.COMBAT
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.ATTACK in cmd_bar.commands
            assert Command.FLEE in cmd_bar.commands
            assert Command.USE_ITEM in cmd_bar.commands

    async def test_shop_phase_shows_browse_and_leave(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.BROWSE in cmd_bar.commands
            assert Command.LEAVE in cmd_bar.commands
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/tui/test_screens.py -v`
Expected: All 5 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/tui/test_screens.py
git commit -m "test: add TitleScreen and GameScreen phase interaction tests"
```

---

### Task 2: GameScreen Action Tests

**Files:**
- Modify: `tests/tui/test_screens.py` (append)

- [ ] **Step 1: Write GameScreen action tests**

Append these classes to `tests/tui/test_screens.py`:

```python
class TestGameScreenActions:
    async def test_attack_button_triggers_combat(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)
            pilot.app.engine.state.phase = Phase.COMBAT
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            attack_button = pilot.app.screen.query_one("#cmd-attack")
            await pilot.click(attack_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0

    async def test_flee_button_returns_to_exploring(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)
            pilot.app.engine.state.phase = Phase.COMBAT
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            flee_button = pilot.app.screen.query_one("#cmd-flee")
            await pilot.click(flee_button)
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING
            assert pilot.app.engine.state.combat is None

    async def test_explore_button_enters_new_room(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            explore_button = pilot.app.screen.query_one("#cmd-explore")
            await pilot.click(explore_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 2

    async def test_inventory_button_shows_empty_message(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            inv_button = pilot.app.screen.query_one("#cmd-inventory")
            await pilot.click(inv_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0

    async def test_inventory_button_shows_items(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            from dark_fort.game.models import Item
            from dark_fort.game.enums import ItemType

            pilot.app.engine.state.player.inventory.append(
                Item(name="Potion", type=ItemType.POTION, damage="d6")
            )
            inv_button = pilot.app.screen.query_one("#cmd-inventory")
            await pilot.click(inv_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0

    async def test_leave_button_opens_shop(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "ShopScreen"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/tui/test_screens.py -v`
Expected: All 11 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/tui/test_screens.py
git commit -m "test: add GameScreen action interaction tests"
```

---

### Task 3: ShopScreen and GameOverScreen Tests

**Files:**
- Modify: `tests/tui/test_screens.py` (append)

- [ ] **Step 1: Write ShopScreen and GameOverScreen tests**

Append these classes to `tests/tui/test_screens.py`:

```python
class TestShopScreen:
    async def test_shop_displays_items_on_mount(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "ShopScreen"
            shop_log = pilot.app.screen.query_one("#shop-log")
            assert shop_log.message_count > 0

    async def test_buy_item_deducts_silver(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 20
            pilot.app.engine.state.phase = Phase.SHOP
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == 16

    async def test_leave_shop_returns_to_game_screen(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            assert pilot.app.engine.state.phase == Phase.EXPLORING


class TestGameOverScreen:
    async def test_death_screen_shows_fallen_message(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0
            pilot.app.engine.check_game_over()
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is False

    async def test_victory_screen_shows_victory_message(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]
            pilot.app.engine.check_victory()
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is True

    async def test_restart_resets_engine(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0
            pilot.app.engine.check_game_over()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "TitleScreen"
            assert pilot.app.engine.state.phase == Phase.TITLE
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/tui/test_screens.py -v`
Expected: All 17 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/tui/test_screens.py
git commit -m "test: add ShopScreen and GameOverScreen interaction tests"
```

---

### Task 4: Death and Flee Flow Tests

**Files:**
- Create: `tests/tui/test_flows.py`

- [ ] **Step 1: Write death and flee flow tests**

```python
from dark_fort.game.enums import MonsterTier, Phase
from dark_fort.game.models import CombatState, Monster
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import GameOverScreen, GameScreen


class TestDeathFlow:
    async def test_player_dies_from_combat_damage(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 1
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)
            pilot.app.engine.state.phase = Phase.COMBAT
            await pilot.pause()
            pilot.app.screen._update_commands()
            await pilot.pause()
            attack_button = pilot.app.screen.query_one("#cmd-attack")
            await pilot.click(attack_button)
            await pilot.pause()
            if pilot.app.engine.state.phase == Phase.COMBAT:
                await pilot.click(attack_button)
                await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is False

    async def test_player_dies_when_hp_reaches_zero(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0
            result = pilot.app.engine.check_game_over()
            await pilot.pause()
            assert result.phase == Phase.GAME_OVER
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"


class TestFleeFlow:
    async def test_flee_returns_to_exploring_with_damage(self):
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
            flee_button = pilot.app.screen.query_one("#cmd-flee")
            await pilot.click(flee_button)
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING
            assert pilot.app.engine.state.combat is None
            assert pilot.app.engine.state.player.hp < initial_hp
            cmd_bar = pilot.app.screen.query_one("#cmd-explore")
            assert cmd_bar is not None
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/tui/test_flows.py -v`
Expected: All 3 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/tui/test_flows.py
git commit -m "test: add death and flee end-to-end flow tests"
```

---

### Task 5: Shop and Victory Flow Tests

**Files:**
- Modify: `tests/tui/test_flows.py` (append)

- [ ] **Step 1: Write shop and victory flow tests**

Append these classes to `tests/tui/test_flows.py`:

```python
class TestShopFlow:
    async def test_buy_item_and_leave_shop(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 20
            pilot.app.engine.state.phase = Phase.SHOP
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "ShopScreen"
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == 16
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            assert pilot.app.engine.state.phase == Phase.EXPLORING

    async def test_cannot_buy_without_enough_silver(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 2
            pilot.app.engine.state.phase = Phase.SHOP
            pilot.app.screen._update_commands()
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            initial_silver = pilot.app.engine.state.player.silver
            await pilot.press("8")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == initial_silver


class TestVictoryFlow:
    async def test_all_benefits_claimed_triggers_victory(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]
            result = pilot.app.engine.check_victory()
            await pilot.pause()
            assert result.phase == Phase.VICTORY
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is True

    async def test_victory_screen_shows_explored_count(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]
            pilot.app.engine.check_victory()
            await pilot.pause()
            stats_widgets = list(pilot.app.screen.query(".game-over-stats"))
            assert len(stats_widgets) == 3
```

- [ ] **Step 2: Run all TUI tests to verify they pass**

Run: `uv run pytest tests/tui/ -v`
Expected: All 21 new tests PASS (17 in test_screens.py, 7 in test_flows.py — note: some overlap with existing 3 tests in test_widgets.py)

- [ ] **Step 3: Run full test suite**

Run: `make test`
Expected: All tests PASS

- [ ] **Step 4: Run lint**

Run: `make lint`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add tests/tui/test_flows.py
git commit -m "test: add shop and victory end-to-end flow tests"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Task |
|-----------------|------|
| TitleScreen: Enter starts game | Task 1, Step 1 |
| GameScreen: Exploring phase commands | Task 1, Step 1 |
| GameScreen: Combat phase commands | Task 1, Step 1 |
| GameScreen: Shop phase commands | Task 1, Step 1 |
| GameScreen: Attack button | Task 2, Step 1 |
| GameScreen: Flee button | Task 2, Step 1 |
| GameScreen: Explore button | Task 2, Step 1 |
| GameScreen: Inventory button (empty/items) | Task 2, Step 1 |
| GameScreen: Leave → ShopScreen | Task 2, Step 1 |
| ShopScreen: mount displays items | Task 3, Step 1 |
| ShopScreen: buy item deducts silver | Task 3, Step 1 |
| ShopScreen: leave returns to GameScreen | Task 3, Step 1 |
| GameOverScreen: death display | Task 3, Step 1 |
| GameOverScreen: victory display | Task 3, Step 1 |
| GameOverScreen: restart | Task 3, Step 1 |
| Death flow | Task 4, Step 1 |
| Shop flow | Task 5, Step 1 |
| Flee flow | Task 4, Step 1 |
| Victory flow | Task 5, Step 1 |

All spec requirements covered. No placeholders found. Type signatures match source code. Method names (`_update_commands`, `check_game_over`, `check_victory`, `buy_item`, `leave_shop`) match engine.py and screens.py exactly.
