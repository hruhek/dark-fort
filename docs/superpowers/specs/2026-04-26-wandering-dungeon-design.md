# Wandering the Dungeon — Show Exits After Room Events

## Problem

When the player returns to EXPLORING phase after combat (kill or flee) or after leaving the Void Peddler shop, the room's exits are not displayed. The player must either remember the exits from before the event or press `[M]ove` to see them again.

## Solution

Add exit info to the `ActionResult.messages` of the 3 engine methods that transition back to EXPLORING, matching the existing pattern already established in `move_to_room()`.

## Changes — `src/dark_fort/game/engine.py`

### 1. `attack()` — after combat resolves to EXPLORING

After the monster is defeated and phase switches to EXPLORING, append exits to `result.messages`.

Guard: only when `result.phase == Phase.EXPLORING` (not GAME_OVER).

### 2. `flee()` — after flee resolves

After phase is set to EXPLORING, append exits to `result.messages`.

Guard: only when `self.state.phase == Phase.EXPLORING`.

### 3. `leave_shop()` — after leaving the shop

Include exits in the returned messages alongside "You leave the Void Peddler."

## Tests — `tests/tui/test_screens.py`

Three new async integration tests using `DarkFortApp().run_test()`:

| Test | Approach |
|------|----------|
| `test_exits_displayed_after_killing_monster` | Inject monster with 1 HP, attack once, verify log contains exit info |
| `test_exits_displayed_after_flee` | Inject monster, flee, verify log contains exit info |
| `test_exits_displayed_after_leaving_shop` | Enter shop phase and push ShopScreen, leave, verify new GameScreen log shows exits |

## Non-Goals

- No changes to `move_to_room()` — it already shows exits.
- No changes to `PhaseState` or `Command` enums.
- No TUI-side logic for fetching exits — engine provides them in the ActionResults.
