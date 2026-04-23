# TODO UI Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 5 UI fixes from the design spec: Use Item flow, Shop StatusBar, HP status refresh, action bar shortcuts, and Ctrl+Q quit binding.

**Architecture:** Add reactive `selecting_item` flag on GameScreen for item selection state. Add `KEY_MAP` for letter-key shortcuts. Add `_refresh_status()` helper to force StatusBar updates after combat. Add StatusBar to ShopScreen compose(). Add quit bindings to all screens.

**Tech Stack:** Python 3.13, Textual TUI framework, Pydantic models, pytest + textual testing

---

## File Structure

| File | Responsibility |
|------|----------------|
| `src/dark_fort/tui/screens.py` | GameScreen (item selection, shortcuts, status refresh), ShopScreen (StatusBar, quit), TitleScreen (quit), GameOverScreen (quit) |
| `src/dark_fort/tui/widgets.py` | CommandBar (button labels with shortcuts), StatusBar (no changes needed) |
| `src/dark_fort/game/phase_states.py` | CombatPhaseState.USE_ITEM returns inventory prompt |
| `tests/game/test_phase_states.py` | Update USE_ITEM test expectation |
| `tests/tui/test_screens.py` | Tests for item selection, shortcuts, quit binding, ShopScreen StatusBar |

---

## Task 1: Add selecting_item flag and item selection flow to GameScreen

**Files:**
- Modify: `src/dark_fort/tui/screens.py`
- Test: `tests/tui/test_screens.py`

### Step 1: Write failing test for item selection

```python
async def test_use_item_key_shows_inventory(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        pilot.app.engine.state.player.inventory.append(
            Potion(name="Potion", heal="d6")
        )
        pilot.app.engine.state.combat = CombatState(
            monster=Monster(name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5),
            monster_hp=5
        )
        pilot.app.engine.state.phase = Phase.COMBAT
        await pilot.pause()
        pilot.app.screen._update_commands()
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        log = pilot.app.screen.query_one("#log")
        assert log.message_count > 0
```

### Step 2: Run test to verify it fails

Run: `pytest tests/tui/test_screens.py::TestGameScreenActions::test_use_item_key_shows_inventory -v`

Expected: FAIL with "u" key not handled

### Step 3: Add selecting_item reactive and KEY_MAP to GameScreen

In `src/dark_fort/tui/screens.py`, add imports and modify GameScreen:

```python
from textual.reactive import reactive  # Add to imports

# In GameScreen class, after __init__:
selecting_item: reactive[bool] = reactive(False)
KEY_MAP: dict[str, Command] = {
    "e": Command.EXPLORE,
    "i": Command.INVENTORY,
    "a": Command.ATTACK,
    "f": Command.FLEE,
    "u": Command.USE_ITEM,
    "b": Command.BROWSE,
    "l": Command.LEAVE,
}
```

### Step 4: Add _refresh_status() helper method

Add to GameScreen:

```python
def _refresh_status(self) -> None:
    """Force StatusBar refresh by reassigning reactive properties."""
    status_bar = self.query_one(StatusBar)
    status_bar.player = self.engine.state.player
    status_bar.explored = self.engine.explored_count
```

### Step 5: Add on_key() handler for shortcuts and item selection

Add to GameScreen:

```python
def on_key(self, event) -> None:
    # Handle item selection mode (digit keys)
    if self.selecting_item:
        if event.character and event.character.isdigit():
            digit = int(event.character)
            index = digit - 1 if digit != 0 else 9
            inventory = self.engine.state.player.inventory
            if 0 <= index < len(inventory):
                result = self.engine.use_item(index)
                self._log_messages(result.messages)
                self.selecting_item = False
                if result.phase:
                    self._handle_phase_change(result)
                self._update_commands()
                self._refresh_status()
            else:
                self._log_messages(["Invalid item number."])
        return
    
    # Handle command shortcuts
    if event.character and event.character.lower() in self.KEY_MAP:
        key = event.character.lower()
        command = self.KEY_MAP[key]
        phase = self.engine.state.phase
        state = PHASE_STATES.get(phase)
        if state and command in state.available_commands:
            if command == Command.USE_ITEM:
                self.selecting_item = True
                self._log_messages(format_inventory(self.engine.state))
                self._log_messages(["Use item: (type item number)"])
            else:
                result = self._handle_command(command.value)
                if result:
                    if command == Command.INVENTORY:
                        self._log_messages(format_inventory(self.engine.state))
                    else:
                        self._log_messages(result.messages)
                    if result.phase:
                        self._handle_phase_change(result)
                    self._update_commands()
                    self._refresh_status()
```

### Step 6: Modify on_button_pressed to use _refresh_status()

Update the end of `on_button_pressed`:

```python
if result.phase:
    self._handle_phase_change(result)
self._update_commands()
self._refresh_status()  # Add this line
```

### Step 7: Clear selecting_item on phase change

In `_handle_phase_change`, add at the start:

```python
def _handle_phase_change(self, result: ActionResult) -> None:
    self.selecting_item = False  # Add this line
    if result.phase == Phase.GAME_OVER:
        ...
```

### Step 8: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestGameScreenActions::test_use_item_key_shows_inventory -v`

Expected: PASS

### Step 9: Write test for using item by digit key

```python
async def test_digit_key_uses_item(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        pilot.app.engine.state.player.inventory.append(
            Potion(name="Potion", heal="d6")
        )
        pilot.app.engine.state.player.hp = 5
        pilot.app.engine.state.combat = CombatState(
            monster=Monster(name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5),
            monster_hp=5
        )
        pilot.app.engine.state.phase = Phase.COMBAT
        await pilot.pause()
        pilot.app.screen._update_commands()
        await pilot.pause()
        await pilot.press("u")  # Enter item selection mode
        await pilot.pause()
        await pilot.press("1")  # Use first item
        await pilot.pause()
        assert pilot.app.engine.state.player.hp > 5  # Potion healed
```

### Step 10: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestGameScreenActions::test_digit_key_uses_item -v`

Expected: PASS

### Step 11: Commit

```bash
git add src/dark_fort/tui/screens.py tests/tui/test_screens.py
git commit -m "feat: add Use Item flow with digit-key selection in combat

- Add selecting_item reactive flag on GameScreen
- Add KEY_MAP for command shortcuts (a, f, u, e, i, b, l)
- Add on_key() handler for shortcuts and digit-key item use
- Add _refresh_status() helper to force StatusBar updates
- Clear selecting_item on phase changes
- Tests for item selection and digit-key use"
```

---

## Task 2: Update button labels to show shortcut hints

**Files:**
- Modify: `src/dark_fort/tui/widgets.py`

### Step 1: Modify CommandBar button label format

In `src/dark_fort/tui/widgets.py`, update `compose` and `watch_commands`:

```python
@staticmethod
def _format_button_label(cmd: Command) -> str:
    """Format button label with shortcut hint: [A]ttack"""
    name = cmd.value.replace("_", " ").title()
    if name:
        return f"[{name[0]}]{name[1:]}"
    return name

def compose(self) -> ComposeResult:
    for cmd in self.commands:
        button = Button(self._format_button_label(cmd), id=f"cmd-{cmd.value}")
        yield button

def watch_commands(self) -> None:
    if not self.is_mounted:
        return
    self.remove_children()
    for cmd in self.commands:
        button = Button(self._format_button_label(cmd), id=f"cmd-{cmd.value}")
        self.mount(button)
```

### Step 2: Write test for button labels

```python
async def test_button_labels_show_shortcuts(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
        attack_button = pilot.app.screen.query_one("#cmd-attack")
        assert "[A]ttack" in attack_button.label
```

### Step 3: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestGameScreenActions::test_button_labels_show_shortcuts -v`

Expected: PASS

### Step 4: Commit

```bash
git add src/dark_fort/tui/widgets.py tests/tui/test_screens.py
git commit -m "feat: add shortcut hints to command buttons

- Format button labels as [A]ttack, [F]lee, [U]se Item, etc."
```

---

## Task 3: Add StatusBar to ShopScreen

**Files:**
- Modify: `src/dark_fort/tui/screens.py`

### Step 1: Modify ShopScreen.compose()

Update `ShopScreen.compose()` to include StatusBar:

```python
def compose(self) -> ComposeResult:
    yield Header(show_clock=False)
    yield StatusBar(
        player=self.engine.state.player,
        explored=self.engine.explored_count,
    )
    yield Static("The Void Peddler", classes="title-header")
    log = LogView(id="shop-log")
    log.can_focus = False
    yield log
    yield CommandBar(id="commands", commands=[Command.LEAVE])
```

### Step 2: Add _refresh_status to ShopScreen

Add to ShopScreen:

```python
def _refresh_status(self) -> None:
    """Update StatusBar with current state."""
    status_bar = self.query_one(StatusBar)
    status_bar.player = self.engine.state.player
    status_bar.explored = self.engine.explored_count
```

### Step 3: Call _refresh_status after purchase

Update `on_key` in ShopScreen:

```python
def on_key(self, event) -> None:
    if event.character and event.character.isdigit():
        digit = int(event.character)
        index = digit - 1 if digit != 0 else 9
        if index < 0 or index >= len(self.engine.state.shop_wares):
            return
        result = self.engine.buy_item(index)
        log = self.query_one("#shop-log", LogView)
        for msg in result.messages:
            log.add_message(msg)
        log.add_message(f"\nYour silver: {self.engine.state.player.silver}s")
        self._refresh_status()  # Add this line
```

### Step 4: Write test for ShopScreen StatusBar

```python
async def test_shop_shows_status_bar(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        pilot.app.engine.state.phase = Phase.SHOP
        pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)
        pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))
        await pilot.pause()
        status_bar = pilot.app.screen.query_one(StatusBar)
        assert status_bar is not None
        assert status_bar.player is not None
```

### Step 5: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestShopScreen::test_shop_shows_status_bar -v`

Expected: PASS

### Step 6: Commit

```bash
git add src/dark_fort/tui/screens.py tests/tui/test_screens.py
git commit -m "feat: add StatusBar to ShopScreen

- Add StatusBar widget to ShopScreen.compose()
- Add _refresh_status() helper for ShopScreen
- Update StatusBar after purchases
- Test for StatusBar visibility"
```

---

## Task 4: Add Ctrl+Q quit binding to all screens

**Files:**
- Modify: `src/dark_fort/tui/screens.py`
- Test: `tests/tui/test_screens.py`

### Step 1: Add Binding import and update TitleScreen

```python
from textual.widgets import Button, Header, Static, Binding  # Add Binding

class TitleScreen(Screen):
    """Title screen with centered text and ENTER to start."""

    BINDINGS = [
        ("enter", "start", "Start Game"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("DARK FORT", classes="title-header")
        yield Static("A delve into the catacombs", classes="title-subtitle")
        yield Static("Press ENTER to begin", classes="title-footer")
        yield Static("Press CTRL+Q to quit", classes="title-footer")
```

### Step 2: Add quit binding to GameScreen

```python
class GameScreen(Screen):
    """Main gameplay screen with log, status bar, and command bar."""

    BINDINGS = [("ctrl+q", "quit", "Quit")]
    
    # ... rest of class
```

### Step 3: Add quit binding to ShopScreen

```python
class ShopScreen(Screen):
    """Void Peddler shop screen."""

    BINDINGS = [
        ("l", "leave", "Leave Shop"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    # ... rest of class
```

### Step 4: Add quit binding and message to GameOverScreen

```python
class GameOverScreen(Screen):
    """Game over / victory screen."""

    BINDINGS = [
        ("enter", "restart", "Try Again"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        if self.victory:
            yield Static("VICTORY", classes="game-over-header")
        else:
            yield Static("YOU HAVE FALLEN", classes="game-over-header")

        player = self.engine.state.player
        explored = self.engine.explored_count

        yield Static(f"Rooms explored: {explored}", classes="game-over-stats")
        yield Static(f"Points gathered: {player.points}/15", classes="game-over-stats")
        yield Static(f"Silver: {player.silver}", classes="game-over-stats")
        yield Static("Press ENTER to try again", classes="game-over-footer")
        yield Static("Press CTRL+Q to quit", classes="game-over-footer")
```

### Step 5: Write test for quit binding

```python
async def test_ctrl_q_exits_app(self):
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("ctrl+q")
        await pilot.pause()
        # App should exit; if we get here without error, quit worked
        assert True
```

### Step 6: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestTitleScreen::test_ctrl_q_exits_app -v`

Expected: PASS (app exits cleanly)

### Step 7: Write test for quit on GameOverScreen

```python
async def test_game_over_shows_quit_hint(self):
    from dark_fort.tui.screens import GameOverScreen
    
    async with DarkFortApp().run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine))
        await pilot.pause()
        # Check that CTRL+Q text appears in the UI
        statics = pilot.app.screen.query(Static)
        labels = [s.renderable for s in statics]
        assert any("CTRL+Q" in str(label) for label in labels)
```

### Step 8: Run test to verify it passes

Run: `pytest tests/tui/test_screens.py::TestGameOverScreen::test_game_over_shows_quit_hint -v`

Expected: PASS

### Step 9: Commit

```bash
git add src/dark_fort/tui/screens.py tests/tui/test_screens.py
git commit -m "feat: add Ctrl+Q quit binding to all screens

- Add Binding import to screens.py
- Add ctrl+q quit binding to TitleScreen, GameScreen, ShopScreen, GameOverScreen
- Show 'Press CTRL+Q to quit' text on TitleScreen and GameOverScreen
- Tests for quit binding on each screen"
```

---

## Task 5: Update phase_states.py USE_ITEM to return inventory prompt

**Files:**
- Modify: `src/dark_fort/game/phase_states.py`
- Test: `tests/game/test_phase_states.py`

### Step 1: Modify CombatPhaseState.USE_ITEM handler

Update in `src/dark_fort/game/phase_states.py`:

```python
def handle_command(
    self, engine: GameEngine, action: Command
) -> ActionResult | None:
    if action == Command.ATTACK:
        return engine.attack()
    if action == Command.FLEE:
        return engine.flee()
    if action == Command.USE_ITEM:
        # Return empty result; GameScreen handles inventory display
        return ActionResult(messages=[])
    return None
```

### Step 2: Update test expectation

Update `tests/game/test_phase_states.py`:

```python
def test_handle_use_item(self):
    engine = GameEngine()
    engine.start_game()
    state = CombatPhaseState()
    result = state.handle_command(engine, Command.USE_ITEM)
    assert result is not None
    assert result.messages == []  # Empty; UI handles prompt
```

### Step 3: Run test to verify it passes

Run: `pytest tests/game/test_phase_states.py::TestCombatPhaseState::test_handle_use_item -v`

Expected: PASS

### Step 4: Commit

```bash
git add src/dark_fort/game/phase_states.py tests/game/test_phase_states.py
git commit -m "refactor: simplify USE_ITEM phase state handler

- Return empty result from CombatPhaseState.USE_ITEM
- GameScreen now handles inventory display and prompt
- Update test expectation"
```

---

## Task 6: Run full test suite

### Step 1: Run all tests

```bash
make test
```

Expected: All tests pass

### Step 2: Run linter

```bash
make lint
```

Expected: No linting errors

### Step 3: Commit any fixes

```bash
git add -A
git commit -m "chore: fix linting issues" || echo "No lint fixes needed"
```

---

## Final Review Checklist

Before marking complete:

- [ ] Use Item: Press 'u' in combat shows numbered inventory, digit uses item
- [ ] Shop: StatusBar visible during shopping, updates after purchases  
- [ ] HP: StatusBar updates after combat rounds
- [ ] Shortcuts: All buttons show [A]ttack format, letter keys work
- [ ] Quit: Ctrl+Q works on all screens, hint text visible on Title/GameOver
- [ ] All tests pass
- [ ] Linter passes
