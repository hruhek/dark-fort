# Auto-Show Room Exits

## Problem

After combat, shopping, or other encounters resolve, the player returns to
EXPLORING but must press `M` to see available exits. This breaks the flow of
"dungeon wandering" — the player should always know where they can go next
without an extra keypress.

## Approach

**Approach A: Auto-append exits in engine methods.**

Add a `room_summary_messages()` helper to `GameEngine` that returns a room
description line plus the exit list. Append these messages to `ActionResult`
whenever the game transitions back to the EXPLORING phase. The TUI layer
requires no changes — it just renders the messages it receives.

## Design

### `room_summary_messages()` helper

Returns a list of strings:

```
You are in a square room — Explored
  1. North → Unexplored
  2. South → Explored (oval)
  0. Exit Dungeon
```

- First line: `"You are in a {shape} room — {status}"` where status is
  `"Explored"` or `"Unexplored"`.
- Remaining lines: reuses existing `get_room_exits()` output.
- Entrance room (id 0) includes the `"0. Exit Dungeon"` line.

### Where to auto-append

| Method          | Condition                           | Append summary? |
| --------------- | ----------------------------------- | ---------------- |
| `attack()`      | Monster slain (phase → EXPLORING)   | Yes              |
| `attack()`      | Monster still alive                 | No               |
| `attack()`      | Player dies (phase → GAME_OVER)     | No               |
| `flee()`        | Player survives (phase → EXPLORING) | Yes              |
| `flee()`        | Player dies (phase → GAME_OVER)     | No               |
| `leave_shop()`  | Always (phase → EXPLORING)          | Yes              |
| `move_to_room()`| Room triggers combat/shop           | No (shown later)  |
| `move_to_room()`| Room already explored              | Yes              |
| `move_to_room()`| Room event resolved, → EXPLORING   | Yes              |
| `start_game()`  | Already shows exits, add header    | Yes (header only) |

### TUI changes

None. The TUI renders `ActionResult.messages` verbatim. The `MOVE` command
handler in `phase_states.py` can be reviewed for simplification, but no
required changes.

## Edge Cases

- **GAME_OVER or VICTORY**: No room summary appended.
- **COMBAT continues**: No room summary until combat resolves.
- **SHOP phase**: No room summary — shown after leaving shop.
- **Re-entering explored room**: Full summary shown (including the 1-in-4
  wandering monster check, which is a separate backlog item).

## Testing

### Unit tests (game/, no Textual)

1. `test_room_summary_messages` — returns description + exits for various room
   states (explored, unexplored, entrance with exit dungeon).
2. `test_attack_shows_room_summary_after_kill` — messages include room summary
   after killing a monster.
3. `test_attack_no_room_summary_mid_combat` — monster survives: no summary.
4. `test_attack_no_room_summary_on_death` — player dies (GAME_OVER): no summary.
5. `test_flee_shows_room_summary` — flee returns to EXPLORING: summary shown.
6. `test_flee_no_room_summary_on_death` — flee kills player: no summary.
7. `test_leave_shop_shows_room_summary` — leaving shop includes room info.
8. `test_move_to_explored_room_shows_summary` — re-entering explored room
   shows full summary.
9. `test_move_to_room_with_combat_no_summary` — room triggers combat: summary
   deferred until combat resolves.

### Integration tests (TUI)

Existing flow tests continue passing. No behavioral regression — messages are
only added, never removed.