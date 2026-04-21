# Item Model Inheritance Refactor

Resolves TODOs in `src/dark_fort/game/models.py` (lines 21, 64, 74):
- "Weapon and Armor should inherit Item"
- "do we need this if Weapon inherits Item" (re: `weapon_to_item`)
- "do we need this if Armor inherits Item" (re: `armor_to_item`)

## Problem

`Weapon`, `Armor`, and `Item` are separate Pydantic models with duplicated fields. When items transition between equipped and inventory states, conversion functions (`weapon_to_item`, `armor_to_item`) are needed to bridge the type gap. This is verbose, error-prone, and contradicts the domain model — a weapon IS an item.

Current structure:

```python
class Weapon(BaseModel):
    name: str
    damage: str
    attack_bonus: int = 0

class Armor(BaseModel):
    name: str
    absorb: str = "d4"

class Item(BaseModel):  # duplicates Weapon/Armor fields as optional
    name: str
    type: ItemType
    damage: str | None = None
    attack_bonus: int = 0
    absorb: str | None = None
    uses: int | None = None
```

## Solution: Inheritance Hierarchy

### New model hierarchy

```python
from typing import Annotated, Union
from pydantic import BaseModel, Field

class Item(BaseModel):
    """Base for all game items."""
    name: str

class Weapon(Item):
    type: ItemType = ItemType.WEAPON
    damage: str
    attack_bonus: int = 0

class Armor(Item):
    type: ItemType = ItemType.ARMOR
    absorb: str = "d4"

class Potion(Item):
    type: ItemType = ItemType.POTION
    heal: str  # dice notation, e.g. "d6"

class Scroll(Item):
    type: ItemType = ItemType.SCROLL
    scroll_type: ScrollType

class Rope(Item):
    type: ItemType = ItemType.ROPE

class Cloak(Item):
    type: ItemType = ItemType.CLOAK

AnyItem = Annotated[
    Union[Weapon, Armor, Potion, Scroll, Rope, Cloak],
    Field(discriminator="type"),
]
```

Key changes:
- `Item` base has only `name` — no optional type-specific fields
- Each subclass adds its own fields with proper types (no `str | None`)
- `AnyItem` discriminated union enables correct deserialization of `list[AnyItem]`
- `weapon_to_item()` and `armor_to_item()` are **deleted** — no conversion needed

### Player model

```python
class Player(BaseModel):
    name: str = "Kargunt"
    hp: int = 15
    max_hp: int = 15
    silver: int = 0
    points: int = 0
    weapon: Weapon | None = None
    armor: Armor | None = None
    inventory: list[AnyItem] = Field(default_factory=list)
    cloak_charges: int = 0
    attack_bonus: int = 0
    level_benefits: list[int] = Field(default_factory=list)
    daemon_fights_remaining: int = 0
```

Changes from current:
- `inventory: list[AnyItem]` — discriminated union instead of `list[Item]`
- `scrolls: list[Item]` — **removed** (dead field, never populated)

### Equipping/unequipping simplification

Before:
```python
# Unequipping: convert Weapon -> Item
self.state.player.inventory.append(weapon_to_item(self.state.player.weapon))

# Equipping from inventory: construct new Weapon from Item fields
self.state.player.weapon = Weapon(
    name=item.name, damage=item.damage or "d4", attack_bonus=item.attack_bonus,
)
self.state.player.inventory.pop(index)
```

After:
```python
# Unequipping: Weapon IS an Item, just move it
old_weapon = self.state.player.weapon
self.state.player.inventory.append(old_weapon)

# Equipping from inventory: isinstance check, then move
item = self.state.player.inventory.pop(index)
if isinstance(item, Weapon):
    self.state.player.weapon = item
```

## Scope

In scope:
- Refactor `Item`, `Weapon`, `Armor` models to inheritance hierarchy
- Add `Potion`, `Scroll`, `Rope`, `Cloak` subclasses
- Add `AnyItem` discriminated union type
- Delete `weapon_to_item()` and `armor_to_item()`
- Remove `Player.scrolls` (dead field)
- Update `Player`, `tables.py`, `engine.py`, `rules.py`, `widgets.py`
- Update all tests

Out of scope:
- Other dead fields (Room.connections, GameState.log, ActionResult.choices)
- Gameplay logic changes
- TUI flow changes

## Files changed

| File | Change |
|------|--------|
| `src/dark_fort/game/models.py` | Refactor Item hierarchy, add AnyItem, remove conversion functions, remove Player.scrolls |
| `src/dark_fort/game/tables.py` | Update SHOP_ITEMS entries to use concrete subclasses; WEAPONS_TABLE/ARMOR_TABLE unchanged |
| `src/dark_fort/game/engine.py` | Simplify equip/buy logic — no conversion functions, use isinstance |
| `src/dark_fort/game/rules.py` | Update Item constructions and isinstance checks |
| `src/dark_fort/tui/widgets.py` | Update type references if needed |
| `tests/game/test_models.py` | Remove conversion helper tests, add subclass tests, add AnyItem tests |
| `tests/game/test_engine.py` | Update Item/Weapon/Armor construction patterns |
| `tests/game/test_rules.py` | Update Item construction patterns |
| `tests/game/test_tables.py` | Update SHOP_ITEMS assertions |
| `tests/tui/test_widgets.py` | Update if affected |

## Edge cases and migration details

### Pydantic v2 discriminated unions
The discriminator field (`type`) must be a literal on each subclass. `ItemType` is a `StrEnum` with `auto()` values, so `Weapon.type = ItemType.WEAPON` works as a discriminator.

### Potion.heal replaces Item.damage
Currently potions use `Item(name="Potion", type=ItemType.POTION, damage="d6")`. The `damage` field name is misleading for a healing item. New model: `Potion(name="Potion", heal="d6")`. Usage in `engine.py:use_item` changes from `roll(item.damage or "d6")` to `roll(item.heal)`. Same for `rules.py:apply_level_benefit` line 176.

### Scroll.scroll_type
Currently scrolls are created as `Item(name=scroll_name, type=ItemType.SCROLL)` without a `ScrollType`. In the new model, `Scroll(name=scroll_name, scroll_type=scroll_type)` carries the type directly. The `SCROLLS_TABLE` remains a list of tuples for now, but scroll creation code passes `scroll_type` through.

### Cloak
Currently `Item(name="Cloak of invisibility", type=ItemType.CLOAK)`. Becomes `Cloak(name="Cloak of invisibility")`. Cloak logic in `engine.py` tracks charges on `Player.cloak_charges`, not on the item itself, so `Cloak` has no extra fields beyond `name` and `type`.

### Rope
Currently `Item(name="Rope", type=ItemType.ROPE)`. Becomes `Rope(name="Rope")`. No extra fields needed.