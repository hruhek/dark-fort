# Design: Clean Architecture & Design Patterns

## Date

2026-04-22

## Context

Dark Fort is a single-player TUI dungeon crawl (~1,400 LOC). The `game/` module contains pure domain logic; `tui/` contains Textual screens/widgets. The previous design-patterns spec (2026-04-21) introduced enums, Item Strategy, and Phase States. The codebase now has several remaining architectural issues, and future features will make them worse:

**Future features** (not implemented now, but informing design):
- Save/load
- Room navigation (connections, door choices)
- Random encounters in explored rooms
- Dungeon generation with minimum room count
- Selling items in shop (half price)
- Limited shop stock per item, resetting each encounter

**Current problems:**

1. **UI/game boundary violation** — `phase_states.py` builds display strings (`"  1. [W] Dagger (d6)"`, `"Available wares:"`, `"Press 1-9..."`). Presentation logic lives in the domain layer.
2. **ActionResult has dead fields** — `choices` and `state_delta` are never populated.
3. **Phase transitions scattered** — Engine mutates `state.phase`, PhaseStates return `phase`, TUI responds. No single authority.
4. **Item Strategy incomplete** — `buy_item()` still has `match/case` on item type because placement logic (slot vs inventory) isn't on the item.
5. **Dungeon generation mixed with engine** — `_generate_room()` does room creation + counter bookkeeping. No support for minimum room count or connections.
6. **`resolve_room_event()` takes full GameState** — Hard to test without constructing a complete state; mutates state directly.
7. **No save/load** — Pydantic models make serialization nearly free, but no save/load API exists.

## Goals

- Game layer returns structured data; TUI owns all formatting.
- Adding a new item type requires changing only `game/models.py` (the new subclass).
- Adding a new phase requires only a new `PhaseState` subclass + `Phase` enum member.
- `GameState` carries all data the TUI needs to render — no importing `SHOP_ITEMS` in TUI.
- Save/load works via `GameState.snapshot()` / `GameState.restore()`.
- Dungeon generation is isolated and testable.
- `resolve_room_event` is a pure function with narrow inputs.

## Approach

Nine independent but sequenced changes, applied in order:

1. Trim ActionResult (remove dead fields)
2. Add ActionKind enum (future-ready, not used yet)
3. Add `equip_slot` to Item subclasses, simplify `buy_item()`
4. Enrich GameState (add `shop_wares`, populate on shop enter/leave)
5. Create `tui/display.py` (format_inventory, format_shop_wares, TYPE_PREFIXES)
6. Clean `phase_states.py` (remove all display strings, return minimal ActionResult)
7. Create `game/dungeon.py` (DungeonBuilder, engine delegates to it)
8. Narrow `resolve_room_event` (return `RoomEventResult`, engine applies deltas)
9. Add Memento pattern (snapshot/restore on GameState, save/load on GameEngine)

---

## 1. Trim ActionResult

### Problem

`ActionResult` has two fields that are never populated: `choices: list[Command]` and `state_delta: dict[str, Any]`.

### Solution

```python
class ActionResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
```

### Files changed

- `game/models.py` — remove `choices` and `state_delta` fields
- Any code referencing `choices` or `state_delta` (none found)

---

## 2. Add ActionKind Enum

### Problem

Future features (scroll effects, navigation, level-up) will need typed action identification. Defining the enum now ensures consistency and prevents stringly-typed dispatch later.

### Solution

```python
class ActionKind(StrEnum):
    INVENTORY = auto()
    COMBAT = auto()
    SHOP = auto()
    ROOM = auto()
    NAVIGATION = auto()
    LEVEL_UP = auto()

    # Values are internal discriminator tags, not display strings.
    # auto() derives value from name (e.g. INVENTORY -> "inventory").
```

Not used on `ActionResult` yet. When future features need typed event data, `ActionKind` is ready.

### Files changed

- `game/enums.py` — add `ActionKind`

---

## 3. Complete Item Strategy — `equip_slot` Property

### Problem

`engine.buy_item()` has a `match item:` block (6 cases) for placement logic. Adding a new item type requires touching `buy_item()` even though `use_item()` already delegates to the item.

### Solution

Add `EquipSlot` StrEnum and `equip_slot` to `Item` base class. Each subclass declares its slot:

```python
class EquipSlot(StrEnum):
    WEAPON = auto()
    ARMOR = auto()
    NONE = auto()
    SPECIAL = auto()

class Item(BaseModel):
    name: str
    equip_slot: EquipSlot = EquipSlot.NONE

    def use(self, state: GameState, index: int) -> ActionResult: ...
    def display_stats(self) -> str: ...

class Weapon(Item):
    equip_slot: EquipSlot = EquipSlot.WEAPON
    ...

class Armor(Item):
    equip_slot: EquipSlot = EquipSlot.ARMOR
    ...

class Cloak(Item):
    equip_slot: EquipSlot = EquipSlot.SPECIAL
    ...

class Potion(Item):
    equip_slot: EquipSlot = EquipSlot.NONE
    ...

class Scroll(Item):
    equip_slot: EquipSlot = EquipSlot.NONE
    ...

class Rope(Item):
    equip_slot: EquipSlot = EquipSlot.NONE
    ...
```

`buy_item()` collapses to match on `EquipSlot` (4 cases) instead of item type (6+ cases). Adding a new weapon or armor subclass requires zero engine changes — only a new `EquipSlot` member would need engine changes, which is rare.

### Files changed

- `game/enums.py` — add `ActionKind`, `EquipSlot`
- `game/models.py` — add `equip_slot` to `Item` and all subclasses
- `game/engine.py` — simplify `buy_item()` to match on `equip_slot`

---

## 4. Enrich GameState for Rendering

### Problem

The TUI imports `SHOP_ITEMS` directly from `game/tables` and formats it in `ShopScreen.on_mount()`. This couples the TUI to table data and prevents future features (limited stock, sell prices) from flowing through state.

### Solution

Add `shop_wares` to `GameState`. The engine populates it when entering a shop and clears it on leave.

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

When `resolve_room_event` returns `RoomEventResult(phase=Phase.SHOP)`, the engine sets `self.state.shop_wares = list(SHOP_ITEMS)` in `enter_new_room()` while applying the result.
When leaving a shop: `self.state.shop_wares = []` in `leave_shop()`.

Future extensions:
- `ShopEntry` gets `quantity: int` for limited stock
- `ShopEntry` gets `sell_price: int | None` for selling
- Navigation data flows through state similarly

`ShopScreen` reads `engine.state.shop_wares` instead of importing `SHOP_ITEMS`.

### Files changed

- `game/models.py` — add `shop_wares` to `GameState`
- `game/engine.py` — populate `shop_wares` on shop enter, clear on leave
- `tui/screens.py` — `ShopScreen` reads `engine.state.shop_wares`

---

## 5. Create `tui/display.py` — TUI Formatting

### Problem

Display formatting (inventory lists, shop wares, type prefixes) lives in `phase_states.py` and `ShopScreen`. This is presentation logic that should be in the TUI layer.

### Solution

Create `tui/display.py` with formatting functions that take `GameState` and return `list[str]`:

```python
# tui/display.py

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

### Files changed

- `tui/display.py` — **new file** with `format_inventory`, `format_shop_wares`, `TYPE_PREFIXES`

---

## 6. Clean `phase_states.py` — Remove Display Strings

### Problem

`ExploringPhaseState.handle_command(INVENTORY)` builds formatted inventory strings. `ShopPhaseState.handle_command(BROWSE)` builds formatted shop strings. These are TUI concerns.

### Solution

PhaseStates return `ActionResult` with a short log message. The TUI renders full context from `GameState` via display builders.

```python
class ExploringPhaseState(PhaseState):
    def handle_command(self, engine, action):
        if action == Command.EXPLORE:
            return engine.enter_new_room()
        if action == Command.INVENTORY:
            return ActionResult(messages=[])
        return None
```

`GameScreen` intercepts the inventory command and renders via `format_inventory()`:

```python
class GameScreen(Screen):
    def on_button_pressed(self, event):
        ...
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

`ShopScreen.on_mount()` uses `format_shop_wares()` instead of inline formatting.

### Files changed

- `game/phase_states.py` — remove all display formatting strings from `ExploringPhaseState` and `ShopPhaseState`
- `tui/screens.py` — `GameScreen` uses display builders for inventory; `ShopScreen` uses display builders for wares

---

## 7. Create `game/dungeon.py` — DungeonBuilder

### Problem

`GameEngine._generate_room()` mixes room generation with engine bookkeeping (`_room_counter`). No support for minimum room count or room connections.

### Solution

Extract `DungeonBuilder`:

```python
# game/dungeon.py

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
        """Generate a dungeon with at least min_rooms connected rooms."""
        rooms = [self.build_room(is_entrance=True)]
        while len(rooms) < min_rooms:
            room = self.build_room()
            parent = rooms[roll(f"d{len(rooms)}") - 1]
            self.connect(parent, room)
            rooms.append(room)
        return rooms
```

`GameEngine` holds a `DungeonBuilder` instance and delegates room creation to it. `_room_counter` moves to `DungeonBuilder._counter`.

`build_dungeon()` is not called yet (room-by-room exploration is the current flow), but it's ready for when dungeon pre-generation is needed.

### Files changed

- `game/dungeon.py` — **new file** with `DungeonBuilder`
- `game/engine.py` — replace `_generate_room()` with `DungeonBuilder` delegation

---

## 8. Narrow `resolve_room_event` — Return Structured Result

### Problem

`resolve_room_event(state: GameState, room_result: RoomEvent, ...)` takes a full `GameState` and mutates it directly (sets `state.combat`, `state.current_room.explored`, reduces `state.player.hp/silver`). Hard to test without constructing a complete `GameState`.

### Solution

Return a `RoomEventResult` struct. The engine applies deltas to `GameState`:

```python
class RoomEventResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
    combat: CombatState | None = None
    explored: bool = False
    silver_delta: int = 0
    hp_delta: int = 0
```

```python
def resolve_room_event(
    room_result: RoomEvent, player: Player, dice_roll: int | None = None
) -> RoomEventResult:
    """Pure function — returns what happened, doesn't mutate."""
    if room_result == RoomEvent.EMPTY:
        return RoomEventResult(
            messages=["The room is empty. You mark it as explored."],
            explored=True,
        )
    elif room_result == RoomEvent.PIT_TRAP:
        pit_result = resolve_pit_trap(player, dice_roll)
        return RoomEventResult(
            messages=pit_result.messages,
            phase=pit_result.phase,
            explored=not pit_result.phase,
        )
    elif room_result == RoomEvent.WEAK_MONSTER:
        monster = get_weak_monster(roll("d4") - 1)
        return RoomEventResult(
            messages=[f"A {monster.name} stands guard! Attack!"],
            phase=Phase.COMBAT,
            combat=CombatState(monster=monster, monster_hp=monster.hp),
        )
    ...
```

Engine applies result:

```python
result = resolve_room_event(room_result, self.state.player)
messages.extend(result.messages)
if result.combat:
    self.state.combat = result.combat
if result.explored and self.state.current_room:
    self.state.current_room.explored = True
self.state.player.silver += result.silver_delta
self.state.player.hp += result.hp_delta
```

### Files changed

- `game/models.py` — add `RoomEventResult`
- `game/rules.py` — `resolve_room_event` returns `RoomEventResult`, takes `Player` instead of `GameState`
- `game/engine.py` — apply `RoomEventResult` deltas to state

---

## 9. Memento Pattern — Save/Load

### Problem

No save/load exists. `GameState` is Pydantic, making serialization nearly free, but no API exposes it.

### Solution

Add convenience methods to `GameState` and `GameEngine`:

```python
class GameState(BaseModel):
    ...existing fields...

    def snapshot(self) -> dict:
        """Serialize state for save/load."""
        return self.model_dump()

    @classmethod
    def restore(cls, data: dict) -> GameState:
        """Restore state from saved data."""
        return cls.model_validate(data)
```

```python
class GameEngine:
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

### Files changed

- `game/models.py` — add `snapshot()` and `restore()` to `GameState`
- `game/engine.py` — add `save()` and `load()`

---

## Implementation Sequence

1. **Trim ActionResult** — remove `choices` and `state_delta` (simplest, zero risk)
2. **Add ActionKind enum** — to `enums.py`, no behavioral change
3. **Add `equip_slot` to Item** — then simplify `buy_item()`
4. **Enrich GameState** — add `shop_wares`; populate on shop enter, clear on leave
5. **Create `tui/display.py`** — move formatting out of `phase_states.py`
6. **Clean `phase_states.py`** — remove all display strings, return minimal `ActionResult`
7. **Create `game/dungeon.py`** — `DungeonBuilder`, engine delegates to it
8. **Narrow `resolve_room_event`** — return `RoomEventResult`, engine applies deltas
9. **Add Memento** — `snapshot`/`restore` on `GameState`, `save`/`load` on `GameEngine`

Each step leaves the project with passing `make test` and `make lint`.

## What's NOT Changing

- `docs/DARK_FORT.md` (canonical game design document)
- `dice.py`, `tables.py` mechanics
- The overall `game/` vs `tui/` separation of concerns
- `tui/app.py`, `tui/widgets.py`
- `CombatPhaseState` (no display strings to remove)
- Game rules and mechanics (no gameplay changes)

## Success Criteria

- `make test` passes after each change
- `make lint` passes after each change
- `phase_states.py` contains zero display formatting strings
- `ShopScreen` does not import `SHOP_ITEMS` from `tables`
- `resolve_room_event` is testable with just a `Player`, no full `GameState`
- `GameEngine.save()` / `GameEngine.load()` round-trips correctly
- Adding a new weapon/armor subclass requires zero changes to `engine.py`
