# Room Exits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add typed Exit objects to rooms, generate dungeons upfront with cardinal directions, and let the player choose which exit to use.

**Architecture:** Replace `Room.doors` and `Room.connections` with `Room.exits: list[Exit]` (with direction field). `DungeonBuilder.build_dungeon()` generates the full graph on game start. `GameEngine` gets `move_to_room()` instead of `enter_new_room()`. TUI shows numbered exits with direction + explored status.

**Tech Stack:** Python 3.12, Pydantic, Textual, pytest

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/dark_fort/game/models.py` | `Exit` model, update `Room` to use `exits` |
| `src/dark_fort/game/dungeon.py` | `DungeonBuilder` generates connected graph with directions |
| `src/dark_fort/game/enums.py` | Add `Command.MOVE` |
| `src/dark_fort/game/phase_states.py` | Update `ExploringPhaseState` commands |
| `src/dark_fort/game/engine.py` | `start_game` calls `build_dungeon`, `move_to_room`, `get_room_exits` |
| `src/dark_fort/tui/widgets.py` | `CommandBar` renders exit buttons with direction labels |
| `src/dark_fort/tui/screens.py` | `GameScreen` shows exits, handles digit-key navigation in exploring |
| `tests/game/test_models.py` | Test `Exit` and updated `Room` |
| `tests/game/test_dungeon.py` | Test `DungeonBuilder` graph generation |
| `tests/game/test_engine.py` | Test `move_to_room`, `get_room_exits` |
| `tests/tui/test_screens.py` | Test exit display and navigation |

---

## Task 1: Add Exit Model and Update Room Model

**Files:**
- Modify: `src/dark_fort/game/models.py:178-184`
- Test: `tests/game/test_models.py`

- [ ] **Step 1: Write failing test for Exit model**

```python
def test_exit_model():
    from dark_fort.game.models import Exit
    exit = Exit(door_number=1, destination=5, direction="north")
    assert exit.door_number == 1
    assert exit.destination == 5
    assert exit.direction == "north"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_models.py::test_exit_model -v`
Expected: FAIL with "cannot import name 'Exit'"

- [ ] **Step 3: Add Exit model to models.py**

Add before the `Room` class:

```python
class Exit(BaseModel):
    door_number: int
    destination: int
    direction: str
```

- [ ] **Step 4: Update Room model**

Replace the Room class:

```python
class Room(BaseModel):
    id: int
    shape: str
    result: str
    explored: bool = False
    exits: list[Exit] = Field(default_factory=list)
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/game/test_models.py -v`
Expected: PASS (may need to update existing Room tests that reference `doors` or `connections`)

- [ ] **Step 6: Update existing Room tests to use new model**

Find all `Room(...)` instantiations in `test_models.py` that use `doors` or `connections` and remove/update those fields. Add `exits` where needed.

- [ ] **Step 7: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: Some failures in dungeon/engine tests that still reference old Room fields — that's OK, we'll fix them in later tasks.

- [ ] **Step 8: Commit**

```bash
git add src/dark_fort/game/models.py tests/game/test_models.py
git commit -m "feat: add Exit model, update Room to use exits"
```

---

## Task 2: Rewrite DungeonBuilder with Graph Generation

**Files:**
- Modify: `src/dark_fort/game/dungeon.py`
- Test: `tests/game/test_dungeon.py`

- [ ] **Step 1: Write failing test for build_dungeon**

```python
def test_build_dungeon_creates_entrance():
    from dark_fort.game.dungeon import DungeonBuilder
    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    assert len(rooms) >= 1
    entrance = rooms[0]
    assert entrance.explored is True
    assert len(entrance.exits) >= 1  # entrance always has at least 1 door (d4=1 is minimum)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_dungeon.py::test_build_dungeon_creates_entrance -v`
Expected: FAIL — old `build_dungeon` returns list of Rooms with old `doors`/`connections` fields

- [ ] **Step 3: Rewrite DungeonBuilder**

Replace the entire file:

```python
from __future__ import annotations

import random

from dark_fort.game.dice import roll
from dark_fort.game.models import Exit, Room
from dark_fort.game.tables import get_room_shape


DIRECTIONS = ["north", "south", "east", "west"]
OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}


class DungeonBuilder:
    """Builds rooms and their exits with cardinal directions."""

    def __init__(self) -> None:
        self._counter = 0
        self.rooms: dict[int, Room] = {}
        # (x, y) -> room_id for grid placement
        self._grid: dict[tuple[int, int], int] = {}

    def build_room(self, is_entrance: bool = False) -> Room:
        room_id = self._counter
        self._counter += 1
        shape = get_room_shape(roll("d6") + roll("d6"))
        return Room(
            id=room_id,
            shape=shape,
            result="pending",
            explored=is_entrance,
        )

    def build_dungeon(self) -> list[Room]:
        """Generate a connected dungeon graph upfront."""
        entrance = self.build_room(is_entrance=True)
        self.rooms[entrance.id] = entrance
        self._grid[(0, 0)] = entrance.id

        # Entrance gets d4 exits (1-4)
        num_exits = roll("d4")
        self._add_exits(entrance, num_exits)

        return list(self.rooms.values())

    def _add_exits(self, room: Room, count: int) -> None:
        """Add exits to a room, connecting to new or existing rooms."""
        x, y = self._get_room_position(room.id)
        available = self._available_directions(x, y)
        # Only add as many exits as we have available directions
        count = min(count, len(available))
        directions = random.sample(available, count)

        for direction in directions:
            dx, dy = self._direction_delta(direction)
            new_x, new_y = x + dx, y + dy

            if (new_x, new_y) in self._grid:
                # Connect to existing room
                existing_id = self._grid[(new_x, new_y)]
                self._connect(room, self.rooms[existing_id], direction)
            else:
                # Create new room
                new_room = self.build_room()
                self.rooms[new_room.id] = new_room
                self._grid[(new_x, new_y)] = new_room.id
                self._connect(room, new_room, direction)
                # New room gets 1 mandatory back exit + (d4-1) additional
                additional = roll("d4") - 1
                self._add_exits(new_room, additional)

    def _connect(self, room_a: Room, room_b: Room, direction: str) -> None:
        """Create bidirectional exits between two rooms."""
        room_a.exits.append(Exit(
            door_number=len(room_a.exits) + 1,
            destination=room_b.id,
            direction=direction,
        ))
        room_b.exits.append(Exit(
            door_number=len(room_b.exits) + 1,
            destination=room_a.id,
            direction=OPPOSITES[direction],
        ))

    def _get_room_position(self, room_id: int) -> tuple[int, int]:
        for pos, rid in self._grid.items():
            if rid == room_id:
                return pos
        raise ValueError(f"Room {room_id} not found on grid")

    def _available_directions(self, x: int, y: int) -> list[str]:
        """Return directions that don't have a room adjacent already."""
        available = []
        for direction in DIRECTIONS:
            dx, dy = self._direction_delta(direction)
            if (x + dx, y + dy) not in self._grid:
                available.append(direction)
        return available

    @staticmethod
    def _direction_delta(direction: str) -> tuple[int, int]:
        return {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }[direction]
```

- [ ] **Step 4: Run dungeon tests**

Run: `uv run pytest tests/game/test_dungeon.py -v`
Expected: PASS

- [ ] **Step 5: Add more dungeon tests**

```python
def test_build_dungeon_connectivity():
    from dark_fort.game.dungeon import DungeonBuilder
    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    for room in rooms:
        for exit in room.exits:
            dest = builder.rooms[exit.destination]
            assert any(e.destination == room.id for e in dest.exits)

def test_build_dungeon_directions():
    from dark_fort.game.dungeon import DungeonBuilder
    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    for room in rooms:
        for exit in room.exits:
            assert exit.direction in ["north", "south", "east", "west"]
```

- [ ] **Step 6: Run all tests**

Run: `uv run pytest tests/game/test_dungeon.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/dark_fort/game/dungeon.py tests/game/test_dungeon.py
git commit -m "feat: rewrite DungeonBuilder with graph generation and directions"
```

---

## Task 3: Update Enums and Phase States

**Files:**
- Modify: `src/dark_fort/game/enums.py`
- Modify: `src/dark_fort/game/phase_states.py`
- Test: `tests/game/test_phase_states.py`

- [ ] **Step 1: Add Command.MOVE to enums.py**

Add `MOVE = auto()` to the `Command` enum after `INVENTORY`.

- [ ] **Step 2: Update ExploringPhaseState**

Replace `ExploringPhaseState`:

```python
class ExploringPhaseState(PhaseState):
    phase = Phase.EXPLORING
    available_commands = [Command.MOVE, Command.INVENTORY]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.MOVE:
            # MOVE needs a target room_id — handled by GameScreen directly
            return ActionResult(messages=[])
        if action == Command.INVENTORY:
            return ActionResult(messages=[])
        return None
```

- [ ] **Step 3: Run tests**

Run: `uv run pytest tests/game/test_phase_states.py -v`
Expected: PASS (or update tests if they check available_commands)

- [ ] **Step 4: Commit**

```bash
git add src/dark_fort/game/enums.py src/dark_fort/game/phase_states.py tests/game/test_phase_states.py
git commit -m "feat: add Command.MOVE, update ExploringPhaseState"
```

---

## Task 4: Update GameEngine

**Files:**
- Modify: `src/dark_fort/game/engine.py`
- Test: `tests/game/test_engine.py`

- [ ] **Step 1: Write failing test for move_to_room**

```python
def test_move_to_room_explores_new_room():
    from dark_fort.game.engine import GameEngine
    engine = GameEngine()
    engine.start_game()
    # Mock dungeon to have at least 2 rooms
    engine._dungeon = mock_dungeon_with_two_rooms()
    engine.state.rooms = {r.id: r for r in engine._dungeon.rooms.values()}
    engine.state.current_room = engine.state.rooms[0]
    engine.state.phase = Phase.EXPLORING

    next_room_id = engine.state.current_room.exits[0].destination
    result = engine.move_to_room(next_room_id)
    assert result.phase == Phase.EXPLORING  # or whatever the room resolves to
    assert engine.state.rooms[next_room_id].explored is True
```

Actually, let's keep it simpler and test with the real dungeon builder. Write a test that starts the game and then moves to an adjacent room:

```python
def test_move_to_room():
    from dark_fort.game.engine import GameEngine
    engine = GameEngine()
    engine.start_game()
    current = engine.state.current_room
    assert current is not None
    assert len(current.exits) > 0
    next_id = current.exits[0].destination
    result = engine.move_to_room(next_id)
    assert engine.state.current_room.id == next_id
    assert result.messages  # should have room description
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/game/test_engine.py::test_move_to_room -v`
Expected: FAIL — `move_to_room` doesn't exist yet

- [ ] **Step 3: Implement engine changes**

Replace `enter_new_room()` with `move_to_room()` and add `get_room_exits()`. Update `start_game()` to call `build_dungeon()`:

```python
class GameEngine:
    def __init__(self) -> None:
        self.state = GameState(phase=Phase.TITLE)
        self._dungeon = DungeonBuilder()

    @property
    def explored_count(self) -> int:
        return sum(1 for r in self.state.rooms.values() if r.explored)

    def start_game(self) -> ActionResult:
        """Generate dungeon upfront and starting equipment."""
        self.state = GameState(phase=Phase.ENTRANCE)
        self._dungeon = DungeonBuilder()

        weapon, item = generate_starting_equipment()
        self.state.player.weapon = weapon
        self.state.player.silver = roll("d6") + 15

        match item:
            case Armor():
                self.state.player.armor = item
            case Potion() | Scroll():
                self.state.player.inventory.append(item)
            case Cloak():
                self.state.player.inventory.append(item)
                item.charges = roll("d4")

        # Build dungeon upfront
        rooms = self._dungeon.build_dungeon()
        for room in rooms:
            self.state.rooms[room.id] = room

        entrance = rooms[0]
        self.state.current_room = entrance

        messages = [
            f"Your name is {self.state.player.name}.",
            f"HP: {self.state.player.hp}/{self.state.player.max_hp}",
            f"Silver: {self.state.player.silver}",
            f"You start with a {weapon.name} ({weapon.damage}).",
            "You enter the Dark Fort...",
        ]

        entrance_result = roll("d4") - 1
        entrance_msg = ENTRANCE_RESULTS[entrance_result]
        messages.append(entrance_msg)

        match entrance_result:
            case 0:  # Find a random item
                item_roll = roll("d6") - 1
                match ITEMS_TABLE[item_roll]:
                    case "Random weapon":
                        random_item = random.choice(WEAPONS_TABLE)
                    case "Potion":
                        random_item = Potion(name="Potion", heal="d6")
                    case "Rope":
                        random_item = Rope(name="Rope")
                    case "Random scroll":
                        scroll_name, scroll_type, _ = random.choice(SCROLLS_TABLE)
                        random_item = Scroll(
                            name=f"Scroll: {scroll_name}", scroll_type=scroll_type
                        )
                    case "Armor":
                        random_item = Armor(name="Armor", absorb="d4")
                    case "Cloak of invisibility":
                        random_item = Cloak(name="Cloak of invisibility")
                    case _:
                        random_item = Potion(name="Potion", heal="d6")
                self.state.player.inventory.append(random_item)
                messages.append(f"You find a {random_item.name}.")
            case 1:  # A weak monster stands guard
                monster = random.choice(WEAK_MONSTERS)
                self.state.combat = CombatState(monster=monster, monster_hp=monster.hp)
                self.state.phase = Phase.COMBAT
                messages.append(f"A {monster.name} attacks!")
            case 2:  # A dying mystic gives a random scroll
                scroll_name, scroll_type, _ = random.choice(SCROLLS_TABLE)
                scroll = Scroll(name=f"Scroll: {scroll_name}", scroll_type=scroll_type)
                self.state.player.inventory.append(scroll)
                messages.append(f"The mystic gives you a {scroll.name}.")
            case _:  # Quiet — nothing
                pass

        if self.state.phase == Phase.ENTRANCE:
            self.state.phase = Phase.EXPLORING

        # Add exit info to messages
        if self.state.current_room:
            exit_info = self.get_room_exits()
            messages.extend(exit_info)

        return ActionResult(messages=messages, phase=self.state.phase)

    def move_to_room(self, room_id: int) -> ActionResult:
        """Move to an existing room through an exit."""
        room = self.state.rooms.get(room_id)
        if not room:
            return ActionResult(messages=["That exit leads nowhere."])

        self.state.current_room = room

        messages = [
            f"You enter a {room.shape.lower()} room.",
        ]

        if not room.explored and room.result == "pending":
            room_result_idx = roll("d6") - 1
            room_result = ROOM_RESULTS[room_result_idx]

            result = resolve_room_event(room_result, self.state.player)
            messages.extend(result.messages)

            if result.combat:
                self.state.combat = result.combat
            if result.explored:
                room.explored = True
            if result.silver_delta:
                self.state.player.silver += result.silver_delta
            if result.hp_delta:
                self.state.player.hp += result.hp_delta

            final_phase = result.phase or Phase.EXPLORING
            self.state.phase = final_phase

            if final_phase == Phase.SHOP:
                self.state.shop_wares = list(SHOP_ITEMS)
        else:
            # Room already explored — no re-roll for now
            # TODO: 1-in-4 weak monster check — next backlog item
            room.explored = True

        exit_info = self.get_room_exits()
        messages.extend(exit_info)

        return ActionResult(messages=messages, phase=self.state.phase)

    def get_room_exits(self) -> list[str]:
        """Return formatted exit descriptions for the current room."""
        if not self.state.current_room:
            return []

        room = self.state.current_room
        lines = ["Exits:"]
        for exit in room.exits:
            dest = self.state.rooms.get(exit.destination)
            if dest and dest.explored:
                status = f"Explored ({dest.shape})"
            else:
                status = "Unexplored"
            lines.append(f"  {exit.door_number}. {exit.direction.capitalize()} → {status}")
        return lines
```

Also remove the old `_generate_room()` and `enter_new_room()` methods.

- [ ] **Step 4: Run engine tests**

Run: `uv run pytest tests/game/test_engine.py -v`
Expected: PASS (may need to update tests that call `enter_new_room`)

- [ ] **Step 5: Update existing engine tests**

Find all tests that call `engine.enter_new_room()` and replace with `engine.move_to_room(room_id)` where appropriate. Some tests may need to be restructured since rooms are now pre-generated.

- [ ] **Step 6: Run all game tests**

Run: `uv run pytest tests/game/ -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/dark_fort/game/engine.py tests/game/test_engine.py
git commit -m "feat: add move_to_room and get_room_exits, generate dungeon upfront"
```

---

## Task 5: Update TUI — CommandBar and GameScreen

**Files:**
- Modify: `src/dark_fort/tui/widgets.py`
- Modify: `src/dark_fort/tui/screens.py`
- Test: `tests/tui/test_widgets.py`, `tests/tui/test_screens.py`

- [ ] **Step 1: Update CommandBar to render exit buttons**

In `widgets.py`, update `CommandBar` so when `commands` contains `Command.MOVE`, it renders buttons with door info from the engine. Actually, since `GameScreen` already has access to the engine, it's better to have `GameScreen` construct the buttons directly.

Alternatively, keep `CommandBar` generic and pass label/shortcut info. Let's modify `CommandBar` to accept a list of `(command, label)` tuples.

Actually, the simplest approach: `GameScreen._update_commands()` already gets `available_commands` from phase state. When the phase is EXPLORING, instead of just showing `[I]nventory`, it should also show exit buttons. But `CommandBar` buttons are built from `Command` enum values.

Better approach: Add a new `set_exit_buttons(exits)` method to `CommandBar`, or have `GameScreen` dynamically add exit buttons below the command bar. Let's keep it simple: `GameScreen` will log the exits (already handled by `get_room_exits()` in engine), and the `[I]nventory` button stays. The player uses digit keys to select exits.

So the TUI changes are minimal:
- `GameScreen.on_key()`: when in EXPLORING phase, if the player presses a digit and we're NOT in `selecting_item` mode, check if the digit matches a door number. If so, call `move_to_room()`.
- `GameScreen._update_commands()`: when in EXPLORING, show `[I]nventory` only (no `[E]xplore`).
- Remove `Command.EXPLORE` from the KEY_MAP or map it to nothing in EXPLORING.

- [ ] **Step 2: Update GameScreen key handling**

In `on_key()`, after the `selecting_item` block and before the command shortcuts block:

```python
# Handle exit selection in exploring phase
if self.engine.state.phase == Phase.EXPLORING:
    if event.character and event.character.isdigit():
        digit = int(event.character)
        current = self.engine.state.current_room
        if current:
            for exit in current.exits:
                if exit.door_number == digit:
                    result = self.engine.move_to_room(exit.destination)
                    self._log_messages(result.messages)
                    if result.phase:
                        self._handle_phase_change(result)
                    self._update_commands()
                    self._refresh_status()
                    return
            # Digit didn't match any exit
            self._log_messages([f"No exit number {digit}."])
            return
```

- [ ] **Step 3: Update KEY_MAP and available commands**

Remove `"e": Command.EXPLORE` from KEY_MAP.

Update `ExploringPhaseState.available_commands` to `[Command.INVENTORY]` (remove `Command.MOVE` since MOVE is handled by digit keys, not the command bar).

- [ ] **Step 4: Update _update_commands()**

```python
def _update_commands(self) -> None:
    phase = self.engine.state.phase
    phase_state = PHASE_STATES.get(phase)
    commands = phase_state.available_commands if phase_state else []

    cmd_bar = self.query_one("#commands", CommandBar)
    cmd_bar.commands = commands

    status_bar = self.query_one(StatusBar)
    status_bar.player = self.engine.state.player
    status_bar.explored = self.engine.explored_count
```

- [ ] **Step 5: Run TUI tests**

Run: `uv run pytest tests/tui/test_screens.py -v`
Expected: Some tests may fail if they expect `[E]xplore` button or `e` key behavior. Update them.

- [ ] **Step 6: Update TUI tests**

Find tests that press `e` to explore and replace with digit key selection. For example, `test_explore_creates_new_room` becomes `test_move_to_room_through_exit`.

- [ ] **Step 7: Run all TUI tests**

Run: `uv run pytest tests/tui/ -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/dark_fort/tui/screens.py src/dark_fort/tui/widgets.py tests/tui/
git commit -m "feat: TUI digit-key exit selection in exploring phase"
```

---

## Task 6: Integration and Final Verification

- [ ] **Step 1: Run all tests**

Run: `make test`
Expected: PASS

- [ ] **Step 2: Run lint**

Run: `make lint`
Expected: PASS (no errors, all formatted)

- [ ] **Step 3: Manual playtest**

Run: `uv run python -m dark_fort`
Expected: Game starts, shows entrance room with exits, digit keys move between rooms, inventory still works.

- [ ] **Step 4: Update backlog**

Move "room exits" item from `docs/backlog.md` to `docs/backlog_done.md`.
Add "dungeon map display" item to end of `docs/backlog.md`.

- [ ] **Step 5: Final commit**

```bash
git add docs/backlog.md docs/backlog_done.md
git commit -m "docs: update backlog — room exits done, add map display"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| Exit model with direction | Task 1 |
| Room model updated (exits replaces doors/connections) | Task 1 |
| DungeonBuilder graph generation with directions | Task 2 |
| Engine: start_game calls build_dungeon | Task 4 |
| Engine: move_to_room replaces enter_new_room | Task 4 |
| Engine: get_room_exits | Task 4 |
| TUI: show exits with direction + explored status | Task 5 |
| TUI: digit-key selection in exploring phase | Task 5 |
| No minimum room count | Task 2 (algorithm) |
| Dead ends allowed | Task 2 (d4-1 additional exits) |
| Backlog update | Task 6 |

## Placeholder Scan

No placeholders found. All steps include actual code and exact commands.

## Type Consistency

- `Exit` model: `door_number: int`, `destination: int`, `direction: str`
- `Room.exits: list[Exit]`
- `DungeonBuilder._connect()` creates bidirectional `Exit` objects
- `GameEngine.move_to_room(room_id: int) -> ActionResult`
- `GameEngine.get_room_exits() -> list[str]`
- `Command.MOVE` added to enum

All consistent across tasks.
