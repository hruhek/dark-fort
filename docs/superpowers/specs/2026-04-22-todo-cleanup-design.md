# TODO Cleanup Design

Resolve the 4 distinct TODOs found in the game logic layer.

## 1. Introduce `ShopEntry` model (tables.py:95)

**Current:** `SHOP_ITEMS: list[tuple[AnyItem, int]]` — price is a bare int alongside the item, with no type safety or serialization support.

**Change:** Add a `ShopEntry(BaseModel)` to `models.py`:

```python
class ShopEntry(BaseModel):
    item: AnyItem
    price: int

    def display_stats(self) -> str:
        stats = self.item.display_stats()
        stats_str = f" ({stats})" if stats else ""
        return f"{self.item.name}{stats_str} — {self.price}s"
```

Update `SHOP_ITEMS` in `tables.py` to use `ShopEntry` instances. Update all consumers:

- `engine.py:buy_item` — `item, price = SHOP_ITEMS[index]` becomes `entry = SHOP_ITEMS[index]`; use `entry.item`, `entry.price`
- `phase_states.py:ShopPhaseState.handle_command` — use `entry.display_stats()`
- `tui/screens.py:ShopScreen.on_mount` — use `entry.display_stats()`

## 2. Type `handle_command` action parameter as `Command` (phase_states.py:34,64,79)

**Current:** `handle_command(self, engine, action: str)` compares raw strings like `if action == "explore"`.

**Change:** Update `PhaseState.handle_command` signature to accept `action: Command`. Since `Command` is a `StrEnum`, string comparisons already work, but the code should use enum members explicitly:

```python
def handle_command(self, engine: GameEngine, action: Command) -> ActionResult | None:
    if action == Command.EXPLORE:
        ...
```

Update `tui/screens.py:_handle_command` to pass `Command` values. The button dispatch already strips `"cmd-"` prefix producing strings like `"explore"` — since `Command` is a `StrEnum` where `Command.EXPLORE == "explore"`, the simplest fix is to cast: `Command(action)`.

## 3. Document why `Item` is a `BaseModel` (models.py:18)

**Current:** TODO asks about the benefit of `Item(BaseModel)`.

**Replace the TODO comment** with an explanatory note listing the benefits:

```python
# BaseModel enables: discriminated unions (AnyItem), model_dump/model_validate
# for save/load serialization, and runtime validation on deserialization.
class Item(BaseModel):
```

No code changes beyond the comment.

## 4. Remove unused dice convenience functions (dice.py:39)

**Current:** `roll_d4()`, `roll_d6()`, `roll_2d6()` exist but are only referenced in `test_dice.py`. Production code uses `roll("d4")` etc. `chance_in_6` IS used in production.

**Change:**
- Remove `roll_d4`, `roll_d6`, `roll_2d6` from `dice.py`
- Remove the TODO comment
- Update `test_dice.py`: delete the `TestConvenienceFunctions` class entirely (its coverage is redundant with `TestRoll`), and update the import to remove the deleted names

`chance_in_6` stays — it provides domain-readable semantics for X-in-6 probabilities used in `rules.py`.

## Files touched

| File | Changes |
|------|---------|
| `game/models.py` | Add `ShopEntry`, update Item TODO comment |
| `game/tables.py` | Convert `SHOP_ITEMS` to `list[ShopEntry]`, remove TODO |
| `game/phase_states.py` | `action: str` → `action: Command`, use enum comparisons, remove TODOs |
| `game/dice.py` | Remove `roll_d4`, `roll_d6`, `roll_2d6`, remove TODO |
| `game/engine.py` | Update `buy_item` to use `ShopEntry` fields |
| `tui/screens.py` | Update `_handle_command` to cast to `Command`, `ShopScreen.on_mount` to use `ShopEntry` |
| `tests/game/test_dice.py` | Remove `TestConvenienceFunctions`, update import |