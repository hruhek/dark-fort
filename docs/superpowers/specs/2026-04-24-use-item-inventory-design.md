# Design: Use Item from Inventory During Exploration

**Date:** 2026-04-24  
**Topic:** Use item from inventory  
**Status:** Approved

---

## Goal

Allow the player to use items from their inventory during the exploration phase, with the ability to cancel/exit the item selection screen.

## Requirements

1. Player should be able to use an item from inventory during **EXPLORING** phase.
2. Player should be able to exit/cancel the inventory or use item screen.
3. All item types usable during exploration (potions, scrolls, weapons, armor, rope, cloak).
4. TDD must be used for implementation (add rule to AGENTS.md).

## Context

- `use_item(index)` already exists in `GameEngine` and delegates to `item.use(state, index)`.
- Item `use()` methods already exist for all types:
  - Weapon/Armor: equip (swap old to inventory, pop from inventory)
  - Potion: heal and consume (pop from inventory)
  - Scroll: placeholder — says "unroll" and consumes (no effects implemented yet)
  - Rope: no-op, not consumed (passive bonus)
  - Cloak: decrement charges, not consumed
- `USE_ITEM` command is only available in **COMBAT** phase.
- `INVENTORY` command exists but currently just shows the list.
- `selecting_item` reactive flag on `GameScreen` handles the "show inventory + wait for number" flow.
- Currently no way to cancel once `selecting_item = True`.

## Design

### Approach: Extend Phase States (Minimal Change)

Keep the existing `selecting_item` reactive flag on `GameScreen`. Add `INVENTORY` (with use capability) to `ExploringPhaseState` commands. Unify key binding to `i` across both phases. Add Escape key to cancel.

### State & Command Changes

- **Commands**: Remove `USE_ITEM` from `Command` enum. Unify everything under `INVENTORY`.
- **Phase States**:
  - `ExploringPhaseState.commands` → `[EXPLORE, INVENTORY]`
  - `CombatPhaseState.commands` → `[ATTACK, FLEE, INVENTORY]` (replace `USE_ITEM`)
- **Selecting mode**: `selecting_item` reactive flag remains. When `i` is pressed:
  1. `selecting_item = True`
  2. Inventory list + prompt appears in log
  3. Digit keys select and use item
  4. **Escape key** sets `selecting_item = False`, restores normal command mode

### TUI Interaction Flow

**EXPLORING phase:**
1. Player presses `i` → `selecting_item = True`, log shows inventory + `"Use item: (type item number or Esc to cancel)"`
2. Digit key (1-9, 0=10th) → `engine.use_item(index)`, result logged, `selecting_item = False`
3. Escape → `selecting_item = False`, log shows `"Cancelled."`, normal commands restored

**COMBAT phase:**
1. Player presses `i` → same flow as above
2. Digit key → `engine.use_item(index)`, result logged
3. If item use doesn't change phase (e.g. equipping a weapon), `selecting_item = False`, stay in COMBAT
4. Escape → same cancel behavior

**Empty inventory guard:** Pressing `i` with empty inventory logs `"No items in inventory."` and does NOT enter selecting mode.

### Item-Specific Outcomes (No changes to existing behavior)

- Potion: heals, consumed, stays in current phase
- Weapon/Armor: equips, old goes to inventory
- Scroll: consumed (stub behavior) — message updated to: `"You unroll the {name}... (effect not yet implemented)"`
- Rope: no-op message, not consumed
- Cloak: charge decremented, not consumed

### File Changes

**`src/dark_fort/game/enums.py`**:
- Remove `USE_ITEM = "use_item"` from `Command` enum.

**`src/dark_fort/game/phase_states.py`**:
- `ExploringPhaseState.commands` → `[EXPLORE, INVENTORY]`
- `CombatPhaseState.commands` → `[ATTACK, FLEE, INVENTORY]`

**`src/dark_fort/game/models.py`**:
- `Scroll.use()`: update message to include "(effect not yet implemented)".

**`src/dark_fort/tui/screens.py`**:
- Remove `u` from `KEY_MAP`.
- Add Escape key handler: when `selecting_item` is True, set `selecting_item = False` and log `"Cancelled."`.
- Update prompt message to `"Use item: (type item number or Esc to cancel)"`.
- Add empty inventory guard.
- Handle `INVENTORY` command in COMBAT (currently only `USE_ITEM` is handled).

**`AGENTS.md`**:
- Add rule: "ALWAYS use TDD for new features and bug fixes — write failing test first, then make it pass."

### Testing Plan (TDD)

**Game layer tests:**
- Test that `INVENTORY` command exists and `USE_ITEM` does not.
- Test `ExploringPhaseState` includes `INVENTORY`.
- Test `CombatPhaseState` includes `INVENTORY` (not `USE_ITEM`).
- Test `Scroll.use()` includes "not yet implemented" message.

**TUI layer tests:**
- Test `i` key in EXPLORING phase shows inventory + prompt.
- Test `i` key in EXPLORING with empty inventory shows message, does not enter selection.
- Test digit key in selection mode uses item in EXPLORING phase.
- Test Escape key cancels selection in EXPLORING phase.
- Test `i` key in COMBAT phase shows inventory + prompt.
- Test Escape key cancels selection in COMBAT phase.
- Test `u` key no longer works.

### Open Questions / Out of Scope

- Scroll effects implementation: deferred to future backlog item.
- Full scroll effect design: not included.
- InventoryScreen or full-screen inventory: not included (Approach C considered, rejected).

## Decision Log

- **All items usable in exploration**: Decided all item types (weapon, armor, potion, scroll, rope, cloak) should be usable during exploration phase.
- **Escape to cancel**: Escape key is the cancellation mechanism.
- **Single inventory command**: Unified `INVENTORY` command under `i` key across both phases. Removed `USE_ITEM`.
- **UI flow only**: Scroll effects remain stubs — only UI flow changes in this task.
- **TDD required**: User explicitly requested TDD. AGENTS.md rule to be added.
