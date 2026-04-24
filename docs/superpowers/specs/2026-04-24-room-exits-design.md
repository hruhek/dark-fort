# Room Exits — Design Spec

## Background

Currently, the game has no room navigation. `enter_new_room()` always generates a brand-new random room. There is no concept of choosing which door to go through. This spec implements the "room exits" backlog item: each room has exits (doors), and the player can choose which exit to use.

## Goals

- Replace the linear "always new room" flow with a dungeon graph where rooms are connected by exits
- Let the player choose which door/exit to use when exploring
- Generate the dungeon upfront so rooms and their connections exist before the player moves
- Design for future 2D map display by using cardinal directions on exits

## Non-Goals

- Re-entering explored rooms and random encounters (next backlog item)
- Dungeon exit / leveling up flow (future backlog items)
- Multiple dungeons or dungeon naming (future backlog items)
- 2D map display itself (future backlog item — but directions are designed in)

## Architecture

### Data Model

**New `Exit` model:**

```python
class Exit(BaseModel):
    door_number: int     # 1, 2, 3, 4
    destination: int     # destination room ID
    direction: str       # "north", "south", "east", "west"
```

**Changes to `Room`:**

- Remove `doors: int` — replaced by `len(exits)`
- Remove `connections: list[int]` — replaced by `exits`
- Add `exits: list[Exit] = Field(default_factory=list)`

### Dungeon Generation (upfront)

On `start_game()`, `DungeonBuilder.build_dungeon()` generates the entire dungeon graph before play begins.

**Algorithm:**

1. Create entrance room with `d4` exits (1-4), assigned to directions in a fixed order (North, South, East, West)
2. Each exit either connects to an existing room or spawns a new one placed 1 grid step away from its parent
3. New rooms get 1 mandatory exit (back to parent, opposite direction) + additional exits per the DARK_FORT door table:
   - d4=1: 0 additional exits (dead end — only back exit)
   - d4=2: 1 additional exit
   - d4=3 or 4: 2 additional exits
4. New room exits use available cardinal directions, excluding the direction already used for the back exit
5. If all 4 directions from a room are taken, no more exits can be added (prevents grid overlap)
6. No minimum room count — a single-room dungeon is valid
7. All rooms stored in `GameState.rooms` dict upfront

### Engine Changes

**Replace `enter_new_room()` with `move_to_room(room_id)`:**

- Current: always generates a new random room
- New: moves player to an already-existing room in `GameState.rooms`
- If room is unexplored (`room.result == "pending"`), resolve its event via `resolve_room_event()`
- If room is explored, skip event resolution (with `# TODO: 1-in-4 weak monster check — next backlog item`)
- Returns `ActionResult` with room description + exit list

**New `get_room_exits()` method:**

- Returns info about current room's exits for TUI display
- Format: list of `{door_number, direction, destination_room_id, explored: bool, shape: str | None}`

**`start_game()` change:**

- Calls `DungeonBuilder.build_dungeon()` upfront
- Still resolves entrance room's event per DARK_FORT rules
- Sets `current_room` to entrance room

### TUI Changes

**Exploring phase display:**

When in EXPLORING phase, the log shows:

```
You are in a Square room.
1. North → Unexplored
2. South → Explored (Oval)
3. East → Unexplored
```

Known rooms show shape; unexplored rooms show "Unexplored".

**Command changes:**

- Replace `EXPLORE` command with numbered door selection
- Digits 1-4 select a door/exit while in EXPLORING phase
- `INVENTORY` remains available

**CommandBar update:**

- EXPLORING phase shows buttons like `[1] North  [2] South  [3] East` instead of `[E]xplore`
- `[I]nventory` button stays

**Phase state:**

- `ExploringPhaseState.available_commands`: `[Command.MOVE, Command.INVENTORY]`
- `MOVE` command carries a target room_id parameter

### Navigation Flow

1. Player enters exploring phase → sees room description + numbered exits
2. Player presses a door number (1-4) → `move_to_room(destination_id)`
3. If room is unexplored, resolve event → may transition to combat/shop
4. If room is explored, skip event resolution → stay in exploring phase

## Files to Modify

- `src/dark_fort/game/models.py` — add `Exit`, update `Room`
- `src/dark_fort/game/dungeon.py` — rewrite `DungeonBuilder` with graph generation
- `src/dark_fort/game/engine.py` — replace `enter_new_room` with `move_to_room`, add `get_room_exits`, update `start_game`
- `src/dark_fort/game/enums.py` — add `Command.MOVE`, keep `Command.EXPLORE` for backward compat (or remove)
- `src/dark_fort/game/phase_states.py` — update `ExploringPhaseState` commands
- `src/dark_fort/tui/screens.py` — `GameScreen` shows exits and handles digit selection in exploring phase
- `src/dark_fort/tui/widgets.py` — `CommandBar` renders exit buttons

## Testing Strategy

- `test_dungeon.py` — test `DungeonBuilder` graph generation (connectivity, dead ends, directions)
- `test_engine.py` — test `move_to_room`, `get_room_exits`, event resolution on first entry only
- `test_screens.py` — test exit display and digit-key navigation in exploring phase
- `test_models.py` — test `Exit` model and updated `Room`

## Backlog Addition

Add to end of `docs/backlog.md`:

```
# dungeon map display
- [ ] show a 2D map of the dungeon with rooms placed on a grid based on exit directions
```

## Decision Log

| Decision | Rationale |
|----------|-----------|
| Upfront generation | User choice. Enables backtracking and simplifies dungeon state. |
| Numbered doors (1,2,3,4) | Matches existing digit-key UI pattern. Simple to understand. |
| Show explored status on doors | Required for upcoming "wandering" backlog item. Better player experience. |
| Allow dead ends | DARK_FORT rules say d4=1 is "no door". With backtracking, dead ends are viable. |
| Scope = room exits only | User explicitly said "room exits only (recommended)" — no wandering or entrance exit yet. |
| Cardinal directions on exits | Future-proofs for 2D map display. Exits need a direction for grid placement. |
| No minimum room count | User explicitly said "if dungeon has only one room that is OK". Matches future multi-dungeon flow. |
