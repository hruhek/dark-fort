# Random Encounter on Room Re-entry

## Problem

Per the DARK_FORT design doc (line 181): "Re-entering explored/fled rooms: 1-in-4 chance of Weak monster."

Currently, `move_to_room()` in `engine.py` skips all encounter logic when a room is already explored — the player just sees the room summary and stays in EXPLORING phase. No random encounter check exists.

## Design

### Change Location

`src/dark_fort/game/engine.py`, method `move_to_room()`, in the `else` branch (lines 144-146) that handles already-explored rooms.

### Logic

When the player enters an already-explored room:

1. Roll d4
2. On result 1 (1-in-4 chance): spawn a random Weak monster using the existing `get_weak_monster()` function and `roll("d4") - 1` index selection. Set phase to `COMBAT` with a `CombatState`. Return message: "A {monster_name} springs from the shadows!"
3. On result 2-4: return the standard room summary (same behavior as today — no extra message).

### Constraints

- Encounter fires **every time** the player re-enters an explored room (not one-shot per room).
- No extra flavor text on a miss — just the standard room summary.
- No new models, tables, or TUI changes required.
- Reuses existing `roll()`, `get_weak_monster()`, and `CombatState` utilities.

### Testing

Two test cases:

1. Re-enter explored room, encounter fires (mock `roll` to return 1): verify combat phase entered with Weak monster.
2. Re-enter explored room, no encounter (mock `roll` to return 2-4): verify standard room summary returned, phase remains EXPLORING.

## Non-goals

- No changes to flee behavior (already works — fled rooms stay unexplored, so re-entry uses the full room table, not this 1-in-4 mechanic).
- No changes to the Weak monster selection table or combat rules.
- No persistent tracking of whether a room has triggered a random encounter (each re-entry rolls fresh).