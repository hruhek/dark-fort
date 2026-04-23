# TODO UI Fixes Design

5 UI fixes derived from `docs/todo.md`.

## 1. Use Item — Inline LogView Selection

### Problem
Combat phase's USE_ITEM command returns `ActionResult(messages=["Use item: (type item number)"])` but there is no inventory display and no digit-key handler to actually use an item.

### Solution
- Add `selecting_item: reactive[bool]` on `GameScreen`, defaults to `False`.
- When USE_ITEM is triggered, `GameScreen` sets `selecting_item = True` and logs the numbered inventory from `format_inventory()` plus the prompt message.
- When `selecting_item` is `True`, digit keys (1-9) in `GameScreen.on_key()` call `engine.use_item(index - 1)` and log the result. The flag is then cleared.
- Out-of-range digits log "Invalid item number." and keep the flag set.
- Any command key (`A`, `F`, `E`, `I`, etc.) or phase change clears `selecting_item`.
- Change USE_ITEM button label to **[U]se Item** to hint at the shortcut.

### Key interactions
- After using an item in combat, combat continues (monster still alive). The command bar updates to reflect current phase state.
- Using a potion in combat heals, then the player still needs to attack or flee.
- Using equipment (weapon/armor) swaps gear as per existing `Item.use()` logic.

## 2. Shop — Persistent StatusBar

### Problem
`ShopScreen` does not include a `StatusBar` widget, so health/silver/etc. disappear while shopping.

### Solution
- Add `StatusBar` widget to `ShopScreen.compose()`, positioned identically to `GameScreen`.
- On mount, set `status_bar.player = engine.state.player` and `status_bar.explored` from the engine.
- Ensure shop purchases (silver changes) and any status changes update the bar.

## 3. HP Status Update During Combat

### Problem
`StatusBar` uses `reactive[Player | None]`, but combat mutates `player.hp` in-place. Textual's reactive watcher does not detect in-place mutations on the same object reference.

### Solution
- After each combat round result in `GameScreen` (after `attack`, `flee`, `use_item`), explicitly reassign `status_bar.player = engine.state.player` to trigger the reactive watcher.
- Wrap this in a helper method `_refresh_status()` on `GameScreen` that reassigns both `player` and `explored`, and call it after every engine action that may change state.

## 4. Action Bar Shortcuts

### Problem
Commands can only be triggered by clicking buttons. No keyboard shortcuts exist.

### Solution
- Add a `KEY_MAP: dict[str, Command]` constant in `GameScreen`:
  - `e → EXPLORE`, `i → INVENTORY`, `a → ATTACK`, `f → FLEE`, `u → USE_ITEM`, `b → BROWSE`, `l → LEAVE`
- In `GameScreen.on_key()`, if the key (lowercase) is in `KEY_MAP` and the mapped command is in the current phase's `available_commands`, dispatch via `PhaseState.handle_command()`.
- If `selecting_item` is `True`, digit keys take priority (for item selection), not command shortcuts.
- Update button labels to show the shortcut letter in brackets: **[A]ttack**, **[F]lee**, **[U]se Item**, **[E]xplore**, **[I]nventory**, **[B]rowse**, **[L]eave**.

### Conflict avoidance
- Key validation checks `available_commands` for the current phase, so `E` only works during EXPLORING, `A`/`F`/`U` only during COMBAT, etc.
- No global conflicts since each phase has unique first letters.

## 5. Ctrl+Q to Exit

### Problem
No explicit quit key binding exists on any screen. Users have no way to exit from TitleScreen or GameOverScreen without closing the terminal.

### Solution
- Add `BINDINGS = [Binding("ctrl+q", "quit", "Quit")]` to `TitleScreen`, `GameOverScreen`, `ShopScreen`, and `GameScreen`.
- Show "Press CTRL+Q to quit" text on `TitleScreen` (alongside "Press ENTER to begin").
- Show "Press CTRL+Q to quit" text on `GameOverScreen` (alongside "Press ENTER to try again").

## Files to modify

| File | Changes |
|------|---------|
| `src/dark_fort/tui/screens.py` | All 5 fixes: GameScreen (items 1,3,4), ShopScreen (2,5), TitleScreen (5), GameOverScreen (5) |
| `src/dark_fort/tui/widgets.py` | Button label formatting (item 4), StatusBar refresh helper (item 3) |
| `src/dark_fort/game/phase_states.py` | USE_ITEM returns inventory prompt text (item 1) |
| `src/dark_fort/tui/display.py` | No changes expected (format_inventory already exists) |
| `tests/game/test_phase_states.py` | Update USE_ITEM command test expectations |
| `tests/tui/test_screens.py` | Add tests for digit-key item use, action bar shortcuts, ctrl+q, ShopScreen StatusBar |
| `tests/tui/test_flows.py` | Update end-to-end flow tests for new key bindings |

## Branch name

`feature/todo-ui-fixes`
