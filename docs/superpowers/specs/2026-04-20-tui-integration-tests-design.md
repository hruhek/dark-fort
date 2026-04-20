# TUI Integration Tests Design

**Date:** 2026-04-20
**Topic:** TUI screen interaction and end-to-end flow tests

## Overview

Add comprehensive TUI integration tests using `DarkFortApp().run_test()` with async pilot. Split into two files: focused screen interaction tests and end-to-end game flows.

## File 1: `tests/tui/test_screens.py` — Focused Screen Interaction Tests

### TitleScreen
- Pressing Enter starts game, dismisses TitleScreen, pushes GameScreen with initial messages

### GameScreen
- **Exploring phase**: command bar shows Explore + Inventory buttons
- **Combat phase**: command bar shows Attack + Flee + Use Item buttons
- **Shop phase**: command bar shows Browse + Leave buttons
- Attack button press calls engine.attack(), logs messages, updates commands
- Flee button press calls engine.flee(), returns to exploring phase
- Explore button press calls engine.enter_new_room(), logs room generation
- Inventory button press shows inventory messages (or "empty" message)
- Leave button press dismisses GameScreen, pushes ShopScreen (when phase=shop)
- Status bar reactively updates after actions that change player state

### ShopScreen
- Mounting displays shop items and player silver
- Digit key press (1-10) triggers engine.buy_item(index), logs result
- Leave action dismisses ShopScreen, pushes GameScreen with result messages

### GameOverScreen
- Victory=false shows "YOU HAVE FALLEN" with stats
- Victory=true shows "VICTORY" with stats
- Restart action resets engine to new GameEngine, pushes TitleScreen

## File 2: `tests/tui/test_flows.py` — End-to-End Game Flows

### Death Flow
- Start game → set combat state with low-HP monster → attack repeatedly → player HP reaches 0 → GameOverScreen appears

### Shop Flow
- Start game → set phase to shop → mount ShopScreen → buy item via key press → verify silver deducted → leave shop → verify back in GameScreen with exploring phase

### Flee Flow
- Start game → set combat state → press Flee button → verify phase returns to exploring, player took d4 damage

### Victory Flow
- Start game → set all 6 level benefits claimed → trigger victory check → GameOverScreen with victory=true

## Testing Patterns

- Use `pilot.app.engine` to set up state (ty: ignore[unresolved-attribute] per AGENTS.md)
- Use `pilot.click()` or `pilot.press()` for interactions
- Assert screen class names via `pilot.app.screen.__class__.__name__`
- Assert widget state via `query_one()`
- Manipulate engine state directly to avoid randomness (set combat, set silver, set benefits)
- Use `await pilot.pause()` after interactions to let reactive updates settle

## Dependencies

- `dark_fort.tui.app.DarkFortApp`
- `dark_fort.tui.screens` (TitleScreen, GameScreen, ShopScreen, GameOverScreen)
- `dark_fort.tui.widgets` (StatusBar, LogView, CommandBar)
- `dark_fort.game.models` (Player, Monster, CombatState, Weapon)
- `dark_fort.game.enums` (Phase, Command, MonsterTier)
