# Wandering Loop Design

## Problem

After combat ends, the shop closes, or any phase transitions the player back to EXPLORING, room exits are not re-displayed. The player must manually press `m` to see where they can go next, breaking the seamless dungeon-wandering experience.

## Goal

After every transition from a non-EXPLORING phase back to EXPLORING, the player should immediately see the room exits without needing to press any additional key. This completes the wandering loop: enter room → resolve event → see exits → choose next door.

## Approach

Append `get_room_exits()` to the ActionResult messages in three engine methods that transition back to EXPLORING. This is consistent with how `start_game()` and `move_to_room()` already include exit info in their messages.

## Changes

### `src/dark_fort/game/engine.py`

Three methods need exits appended when returning to EXPLORING:

1. **`attack()`** — after combat resolves (monster killed): append `self.get_room_exits()` to result messages when `result.phase == Phase.EXPLORING`.

2. **`flee()`** — when fleeing succeeds (player survives): append `self.get_room_exits()` to result messages when `self.state.phase == Phase.EXPLORING` after flee.

3. **`leave_shop()`** — when leaving the Void Peddler: append `self.get_room_exits()` to messages before returning.

GAME_OVER and VICTORY transitions are excluded — player won't be wandering.

### No TUI changes needed

The TUI already logs all ActionResult messages. Exits appear automatically.

### No model changes needed

`ActionResult` and `get_room_exits()` already exist and work as-is.

## Tests

Add to `tests/game/test_engine.py`:

1. After combat kill with exits available, exits appear in result messages
2. After successful flee with exits available, exits appear in result messages
3. After leaving shop with exits available, exits appear in result messages
4. After combat resulting in GAME_OVER, no exits in messages
5. After flee resulting in GAME_OVER, no exits in messages