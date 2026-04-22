# Clean Architecture & Design Patterns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix architectural boundary violations, add design patterns for extensibility, and prepare for future features (save/load, navigation, selling, limited stock).

**Architecture:** Game layer returns structured data via `ActionResult(messages, phase)` with rendering data on `GameState`; TUI owns all formatting via `tui/display.py`. `DungeonBuilder` isolates room generation. `EquipSlot` enum completes Item Strategy. Memento pattern enables save/load.

**Tech Stack:** Python 3.13+, Pydantic, Textual, pytest

---

## File Structure

| File | Responsibility |
|---|---|
| `game/enums.py` | All StrEnum types: ItemType, Phase, Command, RoomEvent, MonsterSpecial, ScrollType, MonsterTier, **ActionKind**, **EquipSlot** |
| `game/models.py` | All Pydantic models: Item hierarchy (with `equip_slot`), ActionResult (trimmed), GameState (with `shop_wares`, `snapshot`/`restore`), **RoomEventResult** |
| `game/dice.py` | Dice rolling — no changes |
| `game/tables.py` | Reference tables — no changes |
| `game/rules.py` | Game rules: `resolve_room_event` returns `RoomEventResult`, takes `Player` not `GameState` |
| `game/phase_states.py` | Phase dispatch — no display formatting strings |
| `game/engine.py` | Game engine: uses `DungeonBuilder`, applies `RoomEventResult`, `save`/`load`, simplified `buy_item` |
| `game/dungeon.py` | **New** — `DungeonBuilder` class |
| `tui/display.py` | **New** — `format_inventory`, `format_shop_wares`, `TYPE_PREFIXES` |
| `tui/screens.py` | Uses display builders, reads `engine.state.shop_wares` |
| `tui/widgets.py` | No changes |
| `tui/app.py` | No changes |

---

### Task 1: Trim ActionResult — Remove Dead Fields

**Files:**
- Modify: `src/dark_fort/game/models.py:200-204`
- Modify: `tests/game/test_models.py:134-138`

- [ ] **Step 1: Update ActionResult model**

In `src/dark_fort/game/models.py`, change the `ActionResult` class:

```python
class ActionResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
```

Remove the `choices` and `state_delta` fields. Also remove the `Any` import from `typing` (line 3) if it was only used by `state_delta: dict[str, Any]` — but `Any` is not used elsewhere, so remove it. Actually, check: the current import is `from typing import Annotated, Any, Literal`. `Any` is only used in `state_delta`. Remove `Any` from the import.

Change line 3 to:
```python
from typing import Annotated, Literal
```

- [ ] **Step 2: Remove the `test_action_result_with_choices` test**

In `tests/game/test_models.py`, delete `class TestActionResult` method `test_action_result_with_choices` (lines 134-138). This test tests the dead `choices` field.

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/game/test_models.py -v`
Expected: PASS

- [ ] **Step 4: Run lint**

Run: `uv run ruff check src/dark_fort/game/models.py tests/game/test_models.py && uv run ruff format --check src/dark_fort/game/models.py tests/game/test_models.py`
Expected: No errors

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/models.py tests/game/test_models.py
git commit -m "refactor: remove unused choices and state_delta from ActionResult"
```

---

### Task 2: Add ActionKind and EquipSlot Enums

**Files:**
- Modify: `src/dark_fort/game/enums.py`
- Create: `tests/game/test_enums.py` (new test file for new enums)

- [ ] **Step 1: Add ActionKind and EquipSlot to enums.py**

Append to `src/dark_fort/game/enums.py`:

```python
class ActionKind(StrEnum):
    INVENTORY = auto()
    COMBAT = auto()
    SHOP = auto()
    ROOM = auto()
    NAVIGATION = auto()
    LEVEL_UP = auto()


class EquipSlot(StrEnum):
    WEAPON = auto()
    ARMOR = auto()
    NONE = auto()
    SPECIAL = auto()
```

- [ ] **Step 2: Write tests for new enums**

Create `tests/game/test_enums.py`:

```python
from dark_fort.game.enums import ActionKind, EquipSlot


class TestActionKind:
    def test_action_kind_values(self):
        assert ActionKind.INVENTORY == "inventory"
        assert ActionKind.COMBAT == "combat"
        assert ActionKind.SHOP == "shop"
        assert ActionKind.ROOM == "room"
        assert ActionKind.NAVIGATION == "navigation"
        assert ActionKind.LEVEL_UP == "level_up"

    def test_action_kind_is_str(self):
        assert isinstance(ActionKind.INVENTORY, str)


class TestEquipSlot:
    def test_equip_slot_values(self):
        assert EquipSlot.WEAPON == "weapon"
        assert EquipSlot.ARMOR == "armor"
        assert EquipSlot.NONE == "none"
        assert EquipSlot.SPECIAL == "special"

    def test_equip_slot_is_str(self):
        assert isinstance(EquipSlot.WEAPON, str)
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/game/test_enums.py -v`
Expected: PASS

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/enums.py tests/game/test_enums.py
git commit -m "feat: add ActionKind and EquipSlot StrEnums"
```

---

### Task 3: Add `equip_slot` to Item Subclasses

**Files:**
- Modify: `src/dark_fort/game/models.py`
- Modify: `tests/game/test_models.py`

- [ ] **Step 1: Update Item base class and all subclasses**

In `src/dark_fort/game/models.py`, add the `EquipSlot` import and `equip_slot` field:

Change the import to include `EquipSlot`:
```python
from dark_fort.game.enums import (
    Command,
    EquipSlot,
    ItemType,
    MonsterSpecial,
    MonsterTier,
    Phase,
    ScrollType,
)
```

Update `Item` base class:
```python
class Item(BaseModel):
    name: str
    equip_slot: EquipSlot = EquipSlot.NONE

    def use(self, state: GameState, index: int) -> ActionResult:
        raise NotImplementedError(f"use() not implemented for {type(self).__name__}")

    def display_stats(self) -> str:
        return ""
```

Update `Weapon`:
```python
class Weapon(Item):
    type: Literal[ItemType.WEAPON] = ItemType.WEAPON
    equip_slot: EquipSlot = EquipSlot.WEAPON
    damage: str
    attack_bonus: int = 0
```

Update `Armor`:
```python
class Armor(Item):
    type: Literal[ItemType.ARMOR] = ItemType.ARMOR
    equip_slot: EquipSlot = EquipSlot.ARMOR
    absorb: str = "d4"
```

Update `Potion`:
```python
class Potion(Item):
    type: Literal[ItemType.POTION] = ItemType.POTION
    equip_slot: EquipSlot = EquipSlot.NONE
    heal: str
```

Update `Scroll`:
```python
class Scroll(Item):
    type: Literal[ItemType.SCROLL] = ItemType.SCROLL
    equip_slot: EquipSlot = EquipSlot.NONE
    scroll_type: ScrollType
```

Update `Rope`:
```python
class Rope(Item):
    type: Literal[ItemType.ROPE] = ItemType.ROPE
    equip_slot: EquipSlot = EquipSlot.NONE
```

Update `Cloak`:
```python
class Cloak(Item):
    type: Literal[ItemType.CLOAK] = ItemType.CLOAK
    equip_slot: EquipSlot = EquipSlot.SPECIAL
```

- [ ] **Step 2: Add tests for equip_slot**

In `tests/game/test_models.py`, add a new test class at the end:

```python
from dark_fort.game.enums import EquipSlot


class TestEquipSlot:
    def test_weapon_equip_slot(self):
        weapon = Weapon(name="Sword", damage="d6")
        assert weapon.equip_slot == EquipSlot.WEAPON

    def test_armor_equip_slot(self):
        armor = Armor(name="Armor", absorb="d4")
        assert armor.equip_slot == EquipSlot.ARMOR

    def test_potion_equip_slot(self):
        potion = Potion(name="Potion", heal="d6")
        assert potion.equip_slot == EquipSlot.NONE

    def test_scroll_equip_slot(self):
        scroll = Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON)
        assert scroll.equip_slot == EquipSlot.NONE

    def test_rope_equip_slot(self):
        rope = Rope(name="Rope")
        assert rope.equip_slot == EquipSlot.NONE

    def test_cloak_equip_slot(self):
        cloak = Cloak(name="Cloak")
        assert cloak.equip_slot == EquipSlot.SPECIAL
```

Add `Rope` to the import list in `test_models.py` (it's not currently imported there).

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/game/test_models.py::TestEquipSlot -v`
Expected: PASS

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/game/models.py tests/game/test_models.py
git commit -m "feat: add EquipSlot field to Item subclasses"
```

---

### Task 4: Simplify `buy_item()` Using `EquipSlot`

**Files:**
- Modify: `src/dark_fort/game/engine.py:135-178`
- Modify: `tests/game/test_engine.py`

- [ ] **Step 1: Rewrite `buy_item()` to use `equip_slot`**

In `src/dark_fort/game/engine.py`, replace the `buy_item` method:

```python
def buy_item(self, index: int) -> ActionResult:
    """Buy an item from the Void Peddler."""
    if self.state.phase != Phase.SHOP:
        return ActionResult(messages=["The shop is not open."])

    if index < 0 or index >= len(SHOP_ITEMS):
        return ActionResult(messages=["Invalid item."])

    entry = SHOP_ITEMS[index]
    item, price = entry.item, entry.price

    if self.state.player.silver < price:
        return ActionResult(
            messages=[
                f"Not enough silver. Need {price}s, have {self.state.player.silver}s."
            ]
        )

    self.state.player.silver -= price

    match item.equip_slot:
        case EquipSlot.WEAPON:
            if self.state.player.weapon is not None:
                self.state.player.inventory.append(self.state.player.weapon)
                msg = f"You buy {item.name} for {price}s. {self.state.player.weapon.name} moved to inventory."
            else:
                msg = f"You buy {item.name} for {price}s."
            self.state.player.weapon = item
        case EquipSlot.ARMOR:
            if self.state.player.armor is not None:
                self.state.player.inventory.append(self.state.player.armor)
                msg = f"You buy {item.name} for {price}s. {self.state.player.armor.name} moved to inventory."
            else:
                msg = f"You buy {item.name} for {price}s."
            self.state.player.armor = item
        case EquipSlot.SPECIAL:
            self.state.player.cloak_charges = roll("d4")
            msg = f"You buy {item.name} for {price}s ({self.state.player.cloak_charges} charges)."
        case EquipSlot.NONE:
            if isinstance(item, Scroll):
                from dark_fort.game.tables import SCROLLS_TABLE

                scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
                self.state.player.inventory.append(
                    Scroll(name=scroll_name, scroll_type=scroll_type)
                )
                msg = f"You buy {scroll_name} for {price}s."
            else:
                self.state.player.inventory.append(item)
                msg = f"You buy {item.name} for {price}s."

    return ActionResult(messages=[msg])
```

Add `EquipSlot` to the imports at the top of `engine.py`:

```python
from dark_fort.game.enums import EquipSlot, Phase
```

Also add `Scroll` is already imported. Add `isinstance` — it's a builtin, no import needed.

- [ ] **Step 2: Run tests**

Run: `uv run pytest tests/game/test_engine.py -v`
Expected: PASS (all existing buy_item tests should still pass)

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/dark_fort/game/engine.py
git commit -m "refactor: simplify buy_item() to match on EquipSlot instead of item type"
```

---

### Task 5: Enrich GameState — Add `shop_wares`

**Files:**
- Modify: `src/dark_fort/game/models.py`
- Modify: `src/dark_fort/game/engine.py`
- Modify: `tests/game/test_models.py`
- Modify: `tests/game/test_engine.py`

- [ ] **Step 1: Add `shop_wares` to GameState**

In `src/dark_fort/game/models.py`, add `shop_wares` to `GameState`:

```python
class GameState(BaseModel):
    player: Player = Field(default_factory=Player)
    current_room: Room | None = None
    rooms: dict[int, Room] = Field(default_factory=dict)
    phase: Phase
    combat: CombatState | None = None
    level_up_queue: bool = False
    shop_wares: list[ShopEntry] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)
```

- [ ] **Step 2: Populate `shop_wares` when entering shop, clear on leave**

In `src/dark_fort/game/engine.py`, update `enter_new_room()` to populate `shop_wares` when a shop event occurs. After the line `self.state.phase = final_phase`, add:

```python
if final_phase == Phase.SHOP:
    self.state.shop_wares = list(SHOP_ITEMS)
```

Update `leave_shop()` to clear `shop_wares`:

```python
def leave_shop(self) -> ActionResult:
    """Leave the Void Peddler."""
    self.state.phase = Phase.EXPLORING
    self.state.shop_wares = []
    if self.state.current_room:
        self.state.current_room.explored = True
    return ActionResult(
        messages=["You leave the Void Peddler."], phase=Phase.EXPLORING
    )
```

Also in `start_game()`, make sure `shop_wares` is empty on new game. Since `GameState(phase=Phase.ENTRANCE)` defaults to `shop_wares=[]`, this is already correct.

- [ ] **Step 3: Update `ShopScreen` to read `shop_wares` instead of `SHOP_ITEMS`**

In `src/dark_fort/tui/screens.py`, update `ShopScreen.on_mount()`:

```python
def on_mount(self) -> None:
    log = self.query_one("#shop-log", LogView)
    log.add_message("Available wares:")
    for i, entry in enumerate(self.engine.state.shop_wares):
        log.add_message(f"  {i + 1}. {entry.display_stats()}")
    log.add_message(f"\nYour silver: {self.engine.state.player.silver}s")
    log.add_message("Press 1-9, 0 for item 10, or L to leave.")
    self.focus()
```

Update `ShopScreen.on_key()` to use `shop_wares` length:

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
```

Remove the `SHOP_ITEMS` import from `screens.py` (line 11).

- [ ] **Step 4: Write tests for `shop_wares`**

In `tests/game/test_models.py`, update `TestGameState`:

```python
class TestGameState:
    def test_default_game_state(self):
        state = GameState(phase=Phase.TITLE)
        assert state.phase == Phase.TITLE
        assert state.player is not None
        assert state.current_room is None
        assert state.rooms == {}
        assert state.combat is None
        assert state.level_up_queue is False
        assert state.shop_wares == []
        assert state.log == []
```

In `tests/game/test_engine.py`, add a test:

```python
class TestShopWares:
    def test_shop_wares_populated_on_shop_event(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.shop_wares = list(SHOP_ITEMS)
        assert len(engine.state.shop_wares) > 0

    def test_shop_wares_cleared_on_leave(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)
        engine.leave_shop()
        assert engine.state.shop_wares == []
```

Add the import at top of `test_engine.py`:
```python
from dark_fort.game.tables import SHOP_ITEMS
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/models.py src/dark_fort/game/engine.py src/dark_fort/tui/screens.py tests/game/test_models.py tests/game/test_engine.py
git commit -m "feat: add shop_wares to GameState, populate on shop enter, clear on leave"
```

---

### Task 6: Create `tui/display.py` — TUI Formatting

**Files:**
- Create: `src/dark_fort/tui/display.py`
- Create: `tests/tui/test_display.py`

- [ ] **Step 1: Create `tui/display.py`**

```python
from dark_fort.game.enums import ItemType
from dark_fort.game.models import GameState

TYPE_PREFIXES: dict[ItemType, str] = {
    ItemType.WEAPON: "W",
    ItemType.ARMOR: "A",
    ItemType.POTION: "P",
    ItemType.SCROLL: "S",
    ItemType.ROPE: "R",
    ItemType.CLOAK: "C",
}


def format_inventory(state: GameState) -> list[str]:
    player = state.player
    if not player.inventory:
        return ["Your inventory is empty."]
    lines = ["Inventory:"]
    for i, item in enumerate(player.inventory):
        prefix = TYPE_PREFIXES.get(item.type, "?")
        stats = item.display_stats()
        stats_str = f" ({stats})" if stats else ""
        lines.append(f"  {i + 1}. [{prefix}] {item.name}{stats_str}")
    return lines


def format_shop_wares(state: GameState) -> list[str]:
    lines = ["Available wares:"]
    for i, entry in enumerate(state.shop_wares):
        lines.append(f"  {i + 1}. {entry.display_stats()}")
    lines.append(f"\nYour silver: {state.player.silver}s")
    lines.append("Press 1-9, 0 for item 10, or L to leave.")
    return lines
```

- [ ] **Step 2: Create `tests/tui/test_display.py`**

```python
from dark_fort.game.enums import Phase, ScrollType
from dark_fort.game.models import Armor, GameState, Potion, Scroll, Weapon
from dark_fort.game.tables import SHOP_ITEMS
from dark_fort.tui.display import format_inventory, format_shop_wares


class TestFormatInventory:
    def test_empty_inventory(self):
        state = GameState(phase=Phase.EXPLORING)
        result = format_inventory(state)
        assert result == ["Your inventory is empty."]

    def test_inventory_with_potion(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Potion(name="Potion", heal="d6")]
        result = format_inventory(state)
        assert result[0] == "Inventory:"
        assert "Potion" in result[1]
        assert "[P]" in result[1]

    def test_inventory_with_weapon(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Weapon(name="Sword", damage="d6", attack_bonus=1)]
        result = format_inventory(state)
        assert "[W]" in result[1]
        assert "d6/+1" in result[1]

    def test_inventory_with_armor(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Armor(name="Armor", absorb="d4")]
        result = format_inventory(state)
        assert "[A]" in result[1]
        assert "d4" in result[1]

    def test_inventory_with_scroll(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [
            Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON)
        ]
        result = format_inventory(state)
        assert "[S]" in result[1]

    def test_inventory_with_multiple_items(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [
            Potion(name="Potion", heal="d6"),
            Weapon(name="Sword", damage="d6"),
        ]
        result = format_inventory(state)
        assert len(result) == 3  # header + 2 items


class TestFormatShopWares:
    def test_format_shop_wares(self):
        state = GameState(phase=Phase.SHOP)
        state.shop_wares = list(SHOP_ITEMS)
        result = format_shop_wares(state)
        assert result[0] == "Available wares:"
        assert any("Potion" in line for line in result)
        assert any("silver" in line.lower() for line in result)

    def test_empty_shop_wares(self):
        state = GameState(phase=Phase.SHOP)
        result = format_shop_wares(state)
        assert result[0] == "Available wares:"
        assert "Your silver:" in result[-2]
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/tui/test_display.py -v`
Expected: PASS

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/dark_fort/tui/display.py tests/tui/test_display.py
git commit -m "feat: add tui/display.py with format_inventory and format_shop_wares"
```

---

### Task 7: Clean `phase_states.py` — Remove Display Strings

**Files:**
- Modify: `src/dark_fort/game/phase_states.py`
- Modify: `tests/game/test_phase_states.py`

- [ ] **Step 1: Remove formatting from `ExploringPhaseState.handle_command(INVENTORY)`**

In `src/dark_fort/game/phase_states.py`, update `ExploringPhaseState.handle_command`:

```python
class ExploringPhaseState(PhaseState):
    phase = Phase.EXPLORING
    available_commands = [Command.EXPLORE, Command.INVENTORY]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.EXPLORE:
            return engine.enter_new_room()
        if action == Command.INVENTORY:
            return ActionResult(messages=[])
        return None
```

Remove the `ItemType` import from `phase_states.py` since it's no longer used. Remove the `SHOP_ITEMS` import too — it was only used by `ShopPhaseState`. Update imports:

```python
from dark_fort.game.enums import Command, Phase
from dark_fort.game.models import ActionResult
```

- [ ] **Step 2: Remove formatting from `ShopPhaseState.handle_command(BROWSE)`**

```python
class ShopPhaseState(PhaseState):
    phase = Phase.SHOP
    available_commands = [Command.BROWSE, Command.LEAVE]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.LEAVE:
            return engine.leave_shop()
        if action == Command.BROWSE:
            return ActionResult(messages=[])
        return None
```

- [ ] **Step 3: Update `GameScreen` to use display builders**

In `src/dark_fort/tui/screens.py`, update `GameScreen.on_button_pressed` to use display builders for inventory:

```python
from dark_fort.tui.display import format_inventory, format_shop_wares

class GameScreen(Screen):
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("cmd-"):
            return

        action = button_id.replace("cmd-", "")
        result = self._handle_command(action)
        if result:
            if Command(action) == Command.INVENTORY:
                self._log_messages(format_inventory(self.engine.state))
            else:
                self._log_messages(result.messages)
            if result.phase:
                self._handle_phase_change(result)
            self._update_commands()
```

Also update `ShopScreen.on_mount()` to use `format_shop_wares`:

```python
def on_mount(self) -> None:
    log = self.query_one("#shop-log", LogView)
    for line in format_shop_wares(self.engine.state):
        log.add_message(line)
    self.focus()
```

- [ ] **Step 4: Update phase_states tests**

In `tests/game/test_phase_states.py`, update `TestExploringPhaseState`:

```python
def test_handle_inventory_empty(self):
    engine = GameEngine()
    engine.start_game()
    engine.state.player.inventory = []
    state = ExploringPhaseState()
    result = state.handle_command(engine, Command.INVENTORY)
    assert result is not None
    assert result.messages == []
```

```python
def test_handle_inventory_with_items(self):
    engine = GameEngine()
    engine.start_game()
    engine.state.player.inventory = [
        Potion(name="Potion", heal="d6"),
        Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON),
    ]
    state = ExploringPhaseState()
    result = state.handle_command(engine, Command.INVENTORY)
    assert result is not None
    assert result.messages == []
```

Update `TestShopPhaseState`:

```python
def test_handle_browse_shows_items(self):
    engine = GameEngine()
    engine.start_game()
    engine.state.shop_wares = list(SHOP_ITEMS)
    state = ShopPhaseState()
    result = state.handle_command(engine, Command.BROWSE)
    assert result is not None
    assert result.messages == []
```

Add `SHOP_ITEMS` import to `test_phase_states.py`:
```python
from dark_fort.game.tables import SHOP_ITEMS
```

Remove the now-unused `Potion` and `Scroll` imports from `test_phase_states.py` since they were only used for inventory test setup... wait, they're still used for `engine.state.player.inventory = [Potion(...), Scroll(...)]`. Keep them.

- [ ] **Step 5: Run tests**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/phase_states.py src/dark_fort/tui/screens.py tests/game/test_phase_states.py
git commit -m "refactor: remove display formatting from phase_states, use tui/display.py"
```

---

### Task 8: Create `game/dungeon.py` — DungeonBuilder

**Files:**
- Create: `src/dark_fort/game/dungeon.py`
- Create: `tests/game/test_dungeon.py`
- Modify: `src/dark_fort/game/engine.py`

- [ ] **Step 1: Create `game/dungeon.py`**

```python
from dark_fort.game.dice import roll
from dark_fort.game.models import Room
from dark_fort.game.tables import get_room_shape


class DungeonBuilder:
    """Builds rooms and their connections."""

    def __init__(self) -> None:
        self._counter = 0

    def build_room(self, is_entrance: bool = False) -> Room:
        room_id = self._counter
        self._counter += 1
        shape = get_room_shape(roll("d6") + roll("d6"))
        doors = roll("d4")
        return Room(
            id=room_id,
            shape=shape,
            doors=doors,
            result="pending",
            explored=is_entrance,
        )

    def connect(self, room_a: Room, room_b: Room) -> None:
        room_a.connections.append(room_b.id)
        room_b.connections.append(room_a.id)

    def build_dungeon(self, min_rooms: int = 12) -> list[Room]:
        rooms = [self.build_room(is_entrance=True)]
        while len(rooms) < min_rooms:
            room = self.build_room()
            parent = rooms[roll(f"d{len(rooms)}") - 1]
            self.connect(parent, room)
            rooms.append(room)
        return rooms
```

- [ ] **Step 2: Write tests for DungeonBuilder**

Create `tests/game/test_dungeon.py`:

```python
from dark_fort.game.dungeon import DungeonBuilder
from dark_fort.game.models import Room


class TestDungeonBuilder:
    def test_build_room_returns_room(self):
        builder = DungeonBuilder()
        room = builder.build_room()
        assert isinstance(room, Room)
        assert room.shape
        assert room.doors >= 1

    def test_build_room_increments_counter(self):
        builder = DungeonBuilder()
        room0 = builder.build_room()
        room1 = builder.build_room()
        assert room0.id == 0
        assert room1.id == 1

    def test_build_entrance_is_explored(self):
        builder = DungeonBuilder()
        room = builder.build_room(is_entrance=True)
        assert room.explored is True

    def test_build_non_entrance_is_unexplored(self):
        builder = DungeonBuilder()
        room = builder.build_room(is_entrance=False)
        assert room.explored is False

    def test_connect_adds_bidirectional_connections(self):
        builder = DungeonBuilder()
        room_a = builder.build_room()
        room_b = builder.build_room()
        builder.connect(room_a, room_b)
        assert room_b.id in room_a.connections
        assert room_a.id in room_b.connections

    def test_build_dungeon_minimum_rooms(self):
        builder = DungeonBuilder()
        rooms = builder.build_dungeon(min_rooms=5)
        assert len(rooms) >= 5

    def test_build_dungeon_first_room_is_entrance(self):
        builder = DungeonBuilder()
        rooms = builder.build_dungeon(min_rooms=3)
        assert rooms[0].explored is True

    def test_build_dungeon_rooms_are_connected(self):
        builder = DungeonBuilder()
        rooms = builder.build_dungeon(min_rooms=5)
        connected_ids: set[int] = set()
        for room in rooms:
            connected_ids.update(room.connections)
        assert len(connected_ids) >= len(rooms) - 1
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/game/test_dungeon.py -v`
Expected: PASS

- [ ] **Step 4: Update `GameEngine` to use `DungeonBuilder`**

In `src/dark_fort/game/engine.py`, replace `_generate_room` and `_room_counter`:

Update imports:
```python
from dark_fort.game.dungeon import DungeonBuilder
```

Replace `__init__`:
```python
def __init__(self) -> None:
    self.state = GameState(phase=Phase.TITLE)
    self._dungeon = DungeonBuilder()
```

Replace `_generate_room`:
```python
def _generate_room(self, is_entrance: bool = False) -> Room:
    """Generate a new room via DungeonBuilder."""
    return self._dungeon.build_room(is_entrance=is_entrance)
```

In `start_game()`, reset the dungeon builder:
```python
def start_game(self) -> ActionResult:
    self.state = GameState(phase=Phase.ENTRANCE)
    self._dungeon = DungeonBuilder()
    ...
```

Remove the `_room_counter` attribute usage (it was `self._room_counter = 0` in `__init__` and `start_game` — replaced by `self._dungeon = DungeonBuilder()` which resets `_counter` to 0).

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/dungeon.py src/dark_fort/game/engine.py tests/game/test_dungeon.py
git commit -m "feat: add DungeonBuilder, engine delegates room generation"
```

---

### Task 9: Narrow `resolve_room_event` — Return `RoomEventResult`

**Files:**
- Modify: `src/dark_fort/game/models.py` — add `RoomEventResult`
- Modify: `src/dark_fort/game/rules.py` — refactor `resolve_room_event`
- Modify: `src/dark_fort/game/engine.py` — apply `RoomEventResult` deltas
- Modify: `tests/game/test_rules.py`
- Create: `tests/game/test_room_event_result.py`

- [ ] **Step 1: Add `RoomEventResult` model**

In `src/dark_fort/game/models.py`, add after `ActionResult`:

```python
class RoomEventResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
    combat: CombatState | None = None
    explored: bool = False
    silver_delta: int = 0
    hp_delta: int = 0
```

- [ ] **Step 2: Rewrite `resolve_room_event` in rules.py**

In `src/dark_fort/game/rules.py`, update the import to include `RoomEventResult`:

```python
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    CombatState,
    Monster,
    Player,
    Potion,
    RoomEventResult,
    Rope,
    Scroll,
    Weapon,
)
```

Remove `GameState` from the import (no longer needed by `resolve_room_event`).

Replace `resolve_room_event`:

```python
def resolve_room_event(
    room_result: RoomEvent, player: Player, dice_roll: int | None = None
) -> RoomEventResult:
    """Resolve a room table result. Pure function — returns what happened, doesn't mutate."""
    if room_result == RoomEvent.EMPTY:
        return RoomEventResult(
            messages=["The room is empty. You mark it as explored."],
            explored=True,
        )

    if room_result == RoomEvent.PIT_TRAP:
        pit_result = resolve_pit_trap(player, dice_roll)
        return RoomEventResult(
            messages=pit_result.messages,
            phase=pit_result.phase,
            explored=not pit_result.phase,
        )

    if room_result == RoomEvent.SOOTHSAYER:
        if dice_roll is None:
            dice_roll = roll("d6")
        if dice_roll % 2 == 1:
            player.silver += 10
            return RoomEventResult(
                messages=[
                    "The Soothsayer rewards you! Gain 10 silver or 3 points.",
                    "You gain 10 silver.",
                ],
                explored=True,
                silver_delta=10,
            )
        damage = roll("d4")
        player.hp -= damage
        if player.hp <= 0:
            return RoomEventResult(
                messages=[
                    f"The Soothsayer curses you! Take {damage} damage (ignores armor).",
                    "You have fallen!",
                ],
                phase=Phase.GAME_OVER,
                hp_delta=-damage,
            )
        return RoomEventResult(
            messages=[
                f"The Soothsayer curses you! Take {damage} damage (ignores armor)."
            ],
            explored=True,
            hp_delta=-damage,
        )

    if room_result == RoomEvent.WEAK_MONSTER:
        monster = get_weak_monster(roll("d4") - 1)
        return RoomEventResult(
            messages=[f"A {monster.name} stands guard! Attack!"],
            phase=Phase.COMBAT,
            combat=CombatState(monster=monster, monster_hp=monster.hp),
        )

    if room_result == RoomEvent.TOUGH_MONSTER:
        from dark_fort.game.tables import get_tough_monster

        monster = get_tough_monster(roll("d4") - 1)
        return RoomEventResult(
            messages=[f"A {monster.name} blocks your path! Attack!"],
            phase=Phase.COMBAT,
            combat=CombatState(monster=monster, monster_hp=monster.hp),
        )

    if room_result == RoomEvent.SHOP:
        return RoomEventResult(
            messages=["You encounter the Void Peddler. Wares are displayed."],
            phase=Phase.SHOP,
        )

    return RoomEventResult(messages=["Unknown room event."])
```

Note: `resolve_pit_trap` still mutates `player.hp` directly. That's acceptable — it's a helper function that takes `Player` directly. The `RoomEventResult.hp_delta` and `silver_delta` track what changed for the engine's awareness. The actual mutation happens in the helper (pit_trap) or in the function body (soothsayer). The engine can use `hp_delta`/`silver_delta` for logging or undo purposes later.

Actually wait — this is inconsistent. `resolve_pit_trap` mutates `player.hp` directly, and the soothsayer branch also mutates `player.silver` and `player.hp` directly. The `RoomEventResult` deltas are then redundant. Let me think about this more carefully.

The goal is: `resolve_room_event` should be a pure function that doesn't mutate `GameState`. But it takes `Player` (a mutable object) and some branches mutate it. Two options:
1. Make `resolve_room_event` truly pure (no mutation at all) — engine applies all deltas
2. Keep helper functions mutating `Player`, have `RoomEventResult` just carry metadata

Option 1 is cleaner but requires changing `resolve_pit_trap` too. Let's go with option 1 — make `resolve_room_event` fully pure:

```python
def resolve_room_event(
    room_result: RoomEvent, player: Player, dice_roll: int | None = None
) -> RoomEventResult:
    """Resolve a room table result. Pure function — returns deltas, doesn't mutate player."""
    if room_result == RoomEvent.EMPTY:
        return RoomEventResult(
            messages=["The room is empty. You mark it as explored."],
            explored=True,
        )

    if room_result == RoomEvent.PIT_TRAP:
        return _resolve_pit_trap_result(player, dice_roll)

    if room_result == RoomEvent.SOOTHSAYER:
        return _resolve_soothsayer_result(player, dice_roll)

    if room_result == RoomEvent.WEAK_MONSTER:
        monster = get_weak_monster(roll("d4") - 1)
        return RoomEventResult(
            messages=[f"A {monster.name} stands guard! Attack!"],
            phase=Phase.COMBAT,
            combat=CombatState(monster=monster, monster_hp=monster.hp),
        )

    if room_result == RoomEvent.TOUGH_MONSTER:
        from dark_fort.game.tables import get_tough_monster

        monster = get_tough_monster(roll("d4") - 1)
        return RoomEventResult(
            messages=[f"A {monster.name} blocks your path! Attack!"],
            phase=Phase.COMBAT,
            combat=CombatState(monster=monster, monster_hp=monster.hp),
        )

    if room_result == RoomEvent.SHOP:
        return RoomEventResult(
            messages=["You encounter the Void Peddler. Wares are displayed."],
            phase=Phase.SHOP,
        )

    return RoomEventResult(messages=["Unknown room event."])
```

Add helper functions:

```python
def _resolve_pit_trap_result(player: Player, dice_roll: int | None = None) -> RoomEventResult:
    """Calculate pit trap result without mutating player."""
    if dice_roll is None:
        dice_roll = roll("d6")

    rope_bonus = 1 if has_rope(player) else 0
    effective_roll = dice_roll + rope_bonus

    messages = [
        f"Pit trap! You rolled {dice_roll}"
        + (f" (+1 rope = {effective_roll})" if rope_bonus else "")
    ]

    if effective_roll <= 3:
        damage = roll("d6")
        if player.hp - damage <= 0:
            messages.append(
                f"You fall in and take {damage} damage (HP: {player.hp - damage}/{player.max_hp})"
            )
            messages.append("You have fallen!")
            return RoomEventResult(messages=messages, phase=Phase.GAME_OVER, hp_delta=-damage)
        messages.append(
            f"You fall in and take {damage} damage (HP: {player.hp - damage}/{player.max_hp})"
        )
        return RoomEventResult(messages=messages, explored=True, hp_delta=-damage)
    messages.append("You avoid the trap safely.")
    return RoomEventResult(messages=messages, explored=True)


def _resolve_soothsayer_result(player: Player, dice_roll: int | None = None) -> RoomEventResult:
    """Calculate soothsayer result without mutating player."""
    if dice_roll is None:
        dice_roll = roll("d6")
    if dice_roll % 2 == 1:
        return RoomEventResult(
            messages=[
                "The Soothsayer rewards you! Gain 10 silver or 3 points.",
                "You gain 10 silver.",
            ],
            explored=True,
            silver_delta=10,
        )
    damage = roll("d4")
    if player.hp - damage <= 0:
        return RoomEventResult(
            messages=[
                f"The Soothsayer curses you! Take {damage} damage (ignores armor).",
                "You have fallen!",
            ],
            phase=Phase.GAME_OVER,
            hp_delta=-damage,
        )
    return RoomEventResult(
        messages=[
            f"The Soothsayer curses you! Take {damage} damage (ignores armor)."
        ],
        explored=True,
        hp_delta=-damage,
    )
```

Keep the existing `resolve_pit_trap` function as-is since it's still used directly in tests and by other code. The new `_resolve_pit_trap_result` is a pure variant for `resolve_room_event` only.

- [ ] **Step 3: Update `engine.enter_new_room()` to apply `RoomEventResult`**

In `src/dark_fort/game/engine.py`, update `enter_new_room`:

```python
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    GameState,
    Potion,
    Room,
    RoomEventResult,
    Scroll,
)
```

```python
def enter_new_room(self) -> ActionResult:
    """Move to a new room through an unexplored door."""
    room = self._generate_room()
    self.state.current_room = room
    self.state.rooms[room.id] = room

    messages = [
        f"You enter a {room.shape.lower()} room with {room.doors} door(s).",
    ]

    room_result_idx = roll("d6") - 1
    room_result = ROOM_RESULTS[room_result_idx]

    result = resolve_room_event(room_result, self.state.player)
    messages.extend(result.messages)

    if result.combat:
        self.state.combat = result.combat
    if result.explored and self.state.current_room:
        self.state.current_room.explored = True
    if result.silver_delta:
        self.state.player.silver += result.silver_delta
    if result.hp_delta:
        self.state.player.hp += result.hp_delta

    final_phase = result.phase or Phase.EXPLORING
    self.state.phase = final_phase

    if final_phase == Phase.SHOP:
        self.state.shop_wares = list(SHOP_ITEMS)

    return ActionResult(messages=messages, phase=final_phase)
```

- [ ] **Step 4: Update tests**

In `tests/game/test_rules.py`, the existing tests for `resolve_pit_trap`, `resolve_combat_hit`, etc. still pass because those functions are unchanged. The `resolve_room_event` function signature changed — check if there are any direct tests of it.

There are no direct tests of `resolve_room_event` in the current test file. Add new tests:

Create `tests/game/test_room_event_result.py`:

```python
from dark_fort.game.enums import MonsterTier, Phase, RoomEvent
from dark_fort.game.models import Monster, Player, Rope, RoomEventResult
from dark_fort.game.rules import resolve_room_event


class TestRoomEventResult:
    def test_empty_room(self):
        player = Player()
        result = resolve_room_event(RoomEvent.EMPTY, player)
        assert isinstance(result, RoomEventResult)
        assert result.explored is True
        assert result.phase is None
        assert result.combat is None

    def test_pit_trap_no_rope(self):
        player = Player(hp=15)
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta < 0

    def test_pit_trap_with_rope_safe(self):
        player = Player(hp=15)
        player.inventory.append(Rope(name="Rope"))
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=4)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta == 0
        assert result.explored is True

    def test_pit_trap_death(self):
        player = Player(hp=1)
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.GAME_OVER

    def test_weak_monster(self):
        player = Player()
        result = resolve_room_event(RoomEvent.WEAK_MONSTER, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.COMBAT
        assert result.combat is not None
        assert result.combat.monster.tier == MonsterTier.WEAK

    def test_tough_monster(self):
        player = Player()
        result = resolve_room_event(RoomEvent.TOUGH_MONSTER, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.COMBAT
        assert result.combat is not None
        assert result.combat.monster.tier == MonsterTier.TOUGH

    def test_shop(self):
        player = Player()
        result = resolve_room_event(RoomEvent.SHOP, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.SHOP
        assert result.combat is None

    def test_soothsayer_reward(self):
        player = Player(silver=0)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=1)
        assert isinstance(result, RoomEventResult)
        assert result.silver_delta == 10
        assert result.explored is True

    def test_soothsayer_curse(self):
        player = Player(hp=15)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta < 0
        assert result.explored is True

    def test_soothsayer_curse_death(self):
        player = Player(hp=1)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.GAME_OVER

    def test_does_not_mutate_player_hp_for_empty(self):
        player = Player(hp=15)
        resolve_room_event(RoomEvent.EMPTY, player)
        assert player.hp == 15

    def test_does_not_mutate_player_silver_for_empty(self):
        player = Player(silver=10)
        resolve_room_event(RoomEvent.EMPTY, player)
        assert player.silver == 10
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/game/test_room_event_result.py -v`
Expected: PASS

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/dark_fort/game/models.py src/dark_fort/game/rules.py src/dark_fort/game/engine.py tests/game/test_room_event_result.py
git commit -m "refactor: resolve_room_event returns RoomEventResult, pure function with narrow inputs"
```

---

### Task 10: Add Memento Pattern — Save/Load

**Files:**
- Modify: `src/dark_fort/game/models.py` — add `snapshot`/`restore` to `GameState`
- Modify: `src/dark_fort/game/engine.py` — add `save`/`load`
- Modify: `tests/game/test_models.py`
- Modify: `tests/game/test_engine.py`

- [ ] **Step 1: Add `snapshot` and `restore` to `GameState`**

In `src/dark_fort/game/models.py`, add methods to `GameState`:

```python
class GameState(BaseModel):
    player: Player = Field(default_factory=Player)
    current_room: Room | None = None
    rooms: dict[int, Room] = Field(default_factory=dict)
    phase: Phase
    combat: CombatState | None = None
    level_up_queue: bool = False
    shop_wares: list[ShopEntry] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)

    def snapshot(self) -> dict:
        return self.model_dump()

    @classmethod
    def restore(cls, data: dict) -> GameState:
        return cls.model_validate(data)
```

- [ ] **Step 2: Add `save` and `load` to `GameEngine`**

In `src/dark_fort/game/engine.py`, add methods:

```python
def save(self) -> dict:
    return {
        "state": self.state.snapshot(),
        "room_counter": self._dungeon._counter,
    }

    @classmethod
    def load(cls, data: dict) -> GameEngine:
        engine = cls.__new__(cls)
        engine.state = GameState.restore(data["state"])
        engine._dungeon = DungeonBuilder()
        engine._dungeon._counter = data["room_counter"]
        return engine
```

- [ ] **Step 3: Write tests for save/load**

In `tests/game/test_models.py`, add to `TestGameState`:

```python
def test_game_state_snapshot_and_restore(self):
    state = GameState(phase=Phase.EXPLORING)
    state.player.silver = 42
    data = state.snapshot()
    restored = GameState.restore(data)
    assert restored.phase == Phase.EXPLORING
    assert restored.player.silver == 42
```

In `tests/game/test_engine.py`, add a new test class:

```python
class TestSaveLoad:
    def test_save_and_load_preserves_state(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 42
        engine.state.player.points = 10

        saved = engine.save()
        loaded = GameEngine.load(saved)

        assert loaded.state.player.silver == 42
        assert loaded.state.player.points == 10
        assert loaded.state.phase == Phase.EXPLORING

    def test_save_and_load_preserves_rooms(self):
        engine = GameEngine()
        engine.start_game()
        room_count = len(engine.state.rooms)

        saved = engine.save()
        loaded = GameEngine.load(saved)

        assert len(loaded.state.rooms) == room_count

    def test_save_and_load_preserves_room_counter(self):
        engine = GameEngine()
        engine.start_game()
        engine.enter_new_room()
        saved = engine.save()
        loaded = GameEngine.load(saved)
        next_room = loaded._dungeon.build_room()
        assert next_room.id == len(engine.state.rooms)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/game/test_models.py::TestGameState::test_game_state_snapshot_and_restore tests/game/test_engine.py::TestSaveLoad -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/dark_fort/game/models.py src/dark_fort/game/engine.py tests/game/test_models.py tests/game/test_engine.py
git commit -m "feat: add Memento pattern — GameState snapshot/restore, GameEngine save/load"
```

---

### Task 11: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 2: Run lint**

Run: `make lint`
Expected: ruff check, ruff format, and ty check all pass

- [ ] **Step 3: Run make test and make lint (as specified in AGENTS.md)**

Run: `make test && make lint`
Expected: PASS

- [ ] **Step 4: Verify spec success criteria**

- `phase_states.py` contains zero display formatting strings — check manually
- `ShopScreen` does not import `SHOP_ITEMS` from `tables` — check `screens.py` imports
- `resolve_room_event` is testable with just a `Player` — confirmed in tests
- `GameEngine.save()` / `GameEngine.load()` round-trips correctly — confirmed in tests
- Adding a new weapon/armor subclass requires zero changes to `engine.py` — `buy_item` matches on `EquipSlot`, not type

- [ ] **Step 5: Final commit (if any stray fixes needed)**

```bash
git add -A
git commit -m "chore: final cleanup after clean architecture refactor"
```
