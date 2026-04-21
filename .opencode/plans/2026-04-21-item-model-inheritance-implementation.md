# Item Model Inheritance Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor Weapon/Armor/Item to use Pydantic inheritance, eliminating conversion functions and optional field sprawl.

**Architecture:** `Item` becomes a slim base model with only `name`. Six subclasses (`Weapon`, `Armor`, `Potion`, `Scroll`, `Rope`, `Cloak`) inherit from it, each adding their own typed fields. A discriminated union `AnyItem` enables correct deserialization of `list[AnyItem]` in `Player.inventory`. Conversion functions `weapon_to_item`/`armor_to_item` are deleted since subclasses ARE items.

**Tech Stack:** Python 3.12+, Pydantic v2, pytest

---

### Task 1: Refactor models.py — new hierarchy, delete conversion functions, remove Player.scrolls

**Files:**
- Modify: `src/dark_fort/game/models.py`

- [ ] **Step 1: Rewrite models.py with the new inheritance hierarchy**

Replace the entire content of `src/dark_fort/game/models.py` with:

```python
from __future__ import annotations

from typing import Annotated, Any, Union

from pydantic import BaseModel, Field, field_validator

from dark_fort.game.enums import Command, ItemType, MonsterTier, Phase, ScrollType


class Item(BaseModel):
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
    heal: str


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


class Monster(BaseModel):
    name: str
    tier: MonsterTier
    points: int
    damage: str
    hp: int
    loot: str | None = None
    special: str | None = None


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

    @field_validator("level_benefits")
    @classmethod
    def level_benefits_must_be_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("level_benefits must contain unique values")
        return v


class Room(BaseModel):
    id: int
    shape: str
    doors: int
    result: str
    explored: bool = False
    connections: list[int] = Field(default_factory=list)


class CombatState(BaseModel):
    monster: Monster
    monster_hp: int
    player_turns: int = 0
    daemon_assist: bool = False


class GameState(BaseModel):
    player: Player = Field(default_factory=Player)
    current_room: Room | None = None
    rooms: dict[int, Room] = Field(default_factory=dict)
    phase: Phase
    combat: CombatState | None = None
    level_up_queue: bool = False
    log: list[str] = Field(default_factory=list)


class ActionResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
    choices: list[Command] = Field(default_factory=list)
    state_delta: dict[str, Any] = Field(default_factory=dict)
```

Key changes from current:
- `Weapon`, `Armor` now inherit from `Item` (which has only `name`)
- `Weapon.type` defaults to `ItemType.WEAPON`, `Armor.type` to `ItemType.ARMOR`, etc.
- `Potion.heal` replaces the old `Item.damage` field for potions
- `Scroll.scroll_type` adds `ScrollType` to scrolls
- `Rope` and `Cloak` are simple subclasses with only `name` + `type`
- `AnyItem` discriminated union for `Player.inventory`
- `weapon_to_item()` and `armor_to_item()` **deleted**
- `Player.scrolls` **deleted** (was never populated)
- Old `Item` class with optional `damage`/`absorb`/`uses` fields **deleted**

- [ ] **Step 2: Commit models refactor**

```bash
git add src/dark_fort/game/models.py
git commit -m "refactor: item model inheritance hierarchy

Replace flat Item/Weapon/Armor models with Pydantic inheritance.
Item base has only name; Weapon, Armor, Potion, Scroll, Rope, Cloak
inherit and add typed fields. Add AnyItem discriminated union.
Delete weapon_to_item/armor_to_item conversion functions.
Remove dead Player.scrolls field."
```

---

### Task 2: Update tables.py — SHOP_ITEMS use concrete subclasses

**Files:**
- Modify: `src/dark_fort/game/tables.py`

- [ ] **Step 1: Update imports and SHOP_ITEMS in tables.py**

Replace the import line:
```python
from dark_fort.game.models import Armor, Item, Monster, Weapon
```
with:
```python
from dark_fort.game.models import AnyItem, Armor, Cloak, Monster, Potion, Rope, Scroll, Weapon
```

Replace the `SHOP_ITEMS` list (lines 86-97):
```python
SHOP_ITEMS: list[tuple[AnyItem, int]] = [
    (Potion(name="Potion", heal="d6"), 4),
    (Scroll(name="Random scroll", scroll_type=ScrollType.SUMMON_DAEMON), 7),
    (Weapon(name="Dagger", damage="d4", attack_bonus=1), 6),
    (Weapon(name="Warhammer", damage="d6"), 9),
    (Rope(name="Rope"), 5),
    (Weapon(name="Sword", damage="d6", attack_bonus=1), 12),
    (Weapon(name="Flail", damage="d6+1"), 15),
    (Weapon(name="Mighty Zweihänder", damage="d6+2"), 25),
    (Armor(name="Armor", absorb="d4"), 10),
    (Cloak(name="Cloak of invisibility"), 15),
]
```

Update the `get_shop_item` return type (line 214):
```python
def get_shop_item(index: int) -> tuple[AnyItem, int]:
```

- [ ] **Step 2: Commit tables update**

```bash
git add src/dark_fort/game/tables.py
git commit -m "refactor: update SHOP_ITEMS to use item subclasses"
```

---

### Task 3: Update rules.py — use subclass constructors, isinstance checks

**Files:**
- Modify: `src/dark_fort/game/rules.py`

- [ ] **Step 1: Update imports in rules.py**

Replace lines 1-16:
```python
from dark_fort.game.dice import chance_in_6, roll
from dark_fort.game.enums import ItemType, Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    CombatState,
    GameState,
    Item,
    Monster,
    Player,
    Weapon,
)
from dark_fort.game.tables import (
    SCROLLS_TABLE,
    WEAPONS_TABLE,
    get_weak_monster,
)
```

with:
```python
from dark_fort.game.dice import chance_in_6, roll
from dark_fort.game.enums import ItemType, Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    CombatState,
    GameState,
    Monster,
    Player,
    Potion,
    Rope,
    Scroll,
    Weapon,
)
from dark_fort.game.tables import (
    SCROLLS_TABLE,
    WEAPONS_TABLE,
    get_weak_monster,
)
```

- [ ] **Step 2: Update generate_starting_equipment**

Replace `generate_starting_equipment` (lines 19-34):
```python
def generate_starting_equipment() -> tuple[Weapon, Armor | Potion | Scroll | Cloak]:
    """Roll 1d4 on weapon table and 1d4 on item table."""
    weapon_idx = roll("d4") - 1
    item_idx = roll("d4") - 1

    weapon = WEAPONS_TABLE[weapon_idx]

    item_table: list[Armor | Potion | Scroll | Cloak] = [
        Armor(name="Armor", absorb="d4"),
        Potion(name="Potion", heal="d6"),
        Scroll(name="Scroll: Summon weak daemon", scroll_type=ScrollType.SUMMON_DAEMON),
        Cloak(name="Cloak of invisibility"),
    ]
    item = item_table[item_idx]

    return weapon, item
```

Add `ScrollType` to the import from `dark_fort.game.enums` (line 2):
```python
from dark_fort.game.enums import ItemType, Phase, ScrollType
```

- [ ] **Step 3: Update _resolve_loot**

Replace `_resolve_loot` (lines 116-129):
```python
def _resolve_loot(monster: Monster, player: Player, messages: list[str]) -> None:
    """Handle monster loot drops."""
    if monster.special == "loot_dagger_2_in_6" and chance_in_6(2):
        player.inventory.append(
            Weapon(name="Dagger", damage="d4", attack_bonus=1)
        )
        messages.append("Loot: Dagger")
    elif monster.special == "loot_scroll_2_in_6" and chance_in_6(2):
        scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
        player.inventory.append(Scroll(name=scroll_name, scroll_type=scroll_type))
        messages.append("Loot: Random scroll")
    elif monster.special == "loot_rope_2_in_6" and chance_in_6(2):
        player.inventory.append(Rope(name="Rope"))
        messages.append("Loot: Rope")
```

- [ ] **Step 4: Update apply_level_benefit**

Replace the relevant branches in `apply_level_benefit` (lines 173-181):
```python
    elif benefit_number == 4:
        for _ in range(5):
            player.inventory.append(
                Potion(name="Potion", heal="d6")
            )
    elif benefit_number == 5:
        player.inventory.append(
            Weapon(name="Mighty Zweihänder", damage="d6+2")
        )
```

- [ ] **Step 5: Update has_rope**

Replace `has_rope` (line 272):
```python
def has_rope(player: Player) -> bool:
    return any(isinstance(item, Rope) for item in player.inventory)
```

Note: This also removes the `ItemType.ROPE` import dependency — `has_rope` now uses `isinstance` instead of checking `item.type`.

- [ ] **Step 6: Commit rules.py update**

```bash
git add src/dark_fort/game/rules.py
git commit -m "refactor: update rules.py to use item subclasses"
```

---

### Task 4: Update engine.py — remove conversion functions, use isinstance

**Files:**
- Modify: `src/dark_fort/game/engine.py`

- [ ] **Step 1: Update imports in engine.py**

Replace lines 1-28:
```python
from __future__ import annotations

from dark_fort.game.dice import roll
from dark_fort.game.enums import Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    GameState,
    Potion,
    Room,
    Scroll,
    Weapon,
)
from dark_fort.game.rules import (
    apply_level_benefit,
    check_level_up,
    flee_combat,
    generate_starting_equipment,
    resolve_combat_hit,
    resolve_room_event,
)
from dark_fort.game.tables import (
    ENTRANCE_RESULTS,
    ROOM_RESULTS,
    SHOP_ITEMS,
    get_room_shape,
)
```

Note: Removed `ItemType`, `Item`, `armor_to_item`, `weapon_to_item`. Added `Cloak`, `Potion`, `Scroll`.

- [ ] **Step 2: Update start_game**

Replace lines 47-59:
```python
        weapon, item = generate_starting_equipment()
        self.state.player.weapon = weapon
        self.state.player.silver = roll("d6") + 15

        match item:
            case Armor():
                self.state.player.armor = item
            case Potion():
                self.state.player.inventory.append(item)
            case Scroll():
                self.state.player.inventory.append(item)
            case Cloak():
                self.state.player.cloak_charges = roll("d4")
```

Note: `isinstance`-style match on class patterns instead of `ItemType` match. No more `Armor(name=item.name, absorb=item.absorb or "d4")` construction.

- [ ] **Step 3: Update buy_item**

Replace lines 133-180:
```python
    def buy_item(self, index: int) -> ActionResult:
        """Buy an item from the Void Peddler."""
        if self.state.phase != Phase.SHOP:
            return ActionResult(messages=["The shop is not open."])

        if index < 0 or index >= len(SHOP_ITEMS):
            return ActionResult(messages=["Invalid item."])

        item, price = SHOP_ITEMS[index]

        if self.state.player.silver < price:
            return ActionResult(
                messages=[
                    f"Not enough silver. Need {price}s, have {self.state.player.silver}s."
                ]
            )

        self.state.player.silver -= price

        match item:
            case Armor():
                if self.state.player.armor is not None:
                    self.state.player.inventory.append(self.state.player.armor)
                    msg = f"You buy {item.name} for {price}s. {self.state.player.armor.name} moved to inventory."
                else:
                    msg = f"You buy {item.name} for {price}s."
                self.state.player.armor = item
            case Cloak():
                self.state.player.cloak_charges = roll("d4")
                msg = f"You buy {item.name} for {price}s ({self.state.player.cloak_charges} charges)."
            case Scroll():
                self.state.player.inventory.append(item)
                msg = f"You buy {item.name} for {price}s."
            case _:
                self.state.player.inventory.append(item)
                msg = f"You buy {item.name} for {price}s."

        return ActionResult(messages=[msg])
```

Key changes:
- `armor_to_item(self.state.player.armor)` → `self.state.player.inventory.append(self.state.player.armor)` — no conversion needed
- `Armor(name=item.name, absorb=item.absorb or "d4")` → `self.state.player.armor = item` — item IS already an Armor
- Scroll purchase: removed `SCROLLS_TABLE` lookup, since `SHOP_ITEMS` now stores `Scroll` objects directly. The "Random scroll" shop item already has a scroll_type; the random roll can be simplified.
- Wait — actually the "Random scroll" in the shop is meant to be random. Let me reconsider.

Actually, looking at the current code more carefully:
```python
case ItemType.SCROLL:
    from dark_fort.game.tables import SCROLLS_TABLE
    scroll_name, _, _ = SCROLLS_TABLE[roll("d4") - 1]
    self.state.player.inventory.append(
        Item(name=scroll_name, type=item.type)
    )
```

The shop's "Random scroll" item triggers a random scroll from SCROLLS_TABLE. The `Scroll` object in `SHOP_ITEMS` would need a placeholder scroll_type, then the engine rolls for the actual one. Two approaches:

**Option A:** Keep the random roll in buy_item, create a new Scroll with the rolled scroll_type:
```python
case Scroll():
    from dark_fort.game.tables import SCROLLS_TABLE
    scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
    self.state.player.inventory.append(
        Scroll(name=scroll_name, scroll_type=scroll_type)
    )
    msg = f"You buy {scroll_name} for {price}s."
```

**Option B:** Use the scroll directly from SHOP_ITEMS and roll for the actual one.

Option A is the cleanest — it matches the current behavior and the scroll_type on the SHOP_ITEMS entry is just a placeholder (SUMMON_DAEMON).

Let me also look at what `generate_starting_equipment` returns for scrolls. Currently it returns `Item(name="Scroll: Summon weak daemon", type=ItemType.SCROLL)`. With the new model, it should return `Scroll(name="Scroll: Summon weak daemon", scroll_type=ScrollType.SUMMON_DAEMON)`.

And in `start_game`, the scroll case is:
```python
case Potion() | Scroll():
    self.state.player.inventory.append(item)
```

This is fine — the item IS a Scroll already, no need to reconstruct it.

OK, final engine.py buy_item:
```python
        match item:
            case Armor():
                if self.state.player.armor is not None:
                    self.state.player.inventory.append(self.state.player.armor)
                    msg = f"You buy {item.name} for {price}s. {self.state.player.armor.name} moved to inventory."
                else:
                    msg = f"You buy {item.name} for {price}s."
                self.state.player.armor = item
            case Cloak():
                self.state.player.cloak_charges = roll("d4")
                msg = f"You buy {item.name} for {price}s ({self.state.player.cloak_charges} charges)."
            case Scroll():
                from dark_fort.game.tables import SCROLLS_TABLE
                scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
                self.state.player.inventory.append(
                    Scroll(name=scroll_name, scroll_type=scroll_type)
                )
                msg = f"You buy {scroll_name} for {price}s."
            case _:
                self.state.player.inventory.append(item)
                msg = f"You buy {item.name} for {price}s."
```

- [ ] **Step 4: Update use_item**

Replace lines 191-251:
```python
    def use_item(self, index: int) -> ActionResult:
        """Use an item from inventory."""
        if index < 0 or index >= len(self.state.player.inventory):
            return ActionResult(messages=["Invalid item index."])

        item = self.state.player.inventory[index]
        messages: list[str] = []

        match item:
            case Potion():
                heal = roll(item.heal)
                self.state.player.hp = min(
                    self.state.player.hp + heal, self.state.player.max_hp
                )
                messages.append(f"You drink the potion and heal {heal} HP.")
                self.state.player.inventory.pop(index)

            case Scroll():
                messages.append(f"You unroll the {item.name}...")
                self.state.player.inventory.pop(index)

            case Weapon():
                if self.state.player.weapon is not None:
                    self.state.player.inventory.append(self.state.player.weapon)
                    messages.append(
                        f"{self.state.player.weapon.name} moved to inventory."
                    )
                self.state.player.weapon = item
                messages.append(f"You equip the {item.name}.")
                self.state.player.inventory.pop(index)

            case Armor():
                if self.state.player.armor is not None:
                    self.state.player.inventory.append(self.state.player.armor)
                    messages.append(
                        f"{self.state.player.armor.name} moved to inventory."
                    )
                self.state.player.armor = item
                messages.append(f"You equip the {item.name}.")
                self.state.player.inventory.pop(index)

            case Cloak():
                self.state.player.cloak_charges = max(
                    0, self.state.player.cloak_charges - 1
                )
                messages.append(
                    f"Cloak activated. {self.state.player.cloak_charges} charges remaining."
                )

        return ActionResult(messages=messages)
```

Key changes:
- `match item.type` → `match item` with `isinstance` patterns
- `weapon_to_item(self.state.player.weapon)` → `self.state.player.inventory.append(self.state.player.weapon)` — direct assignment
- `armor_to_item(self.state.player.armor)` → `self.state.player.inventory.append(self.state.player.armor)` — direct assignment
- `Weapon(name=item.name, damage=item.damage or "d4", attack_bonus=item.attack_bonus)` → `self.state.player.weapon = item` — item IS a Weapon
- `Armor(name=item.name, absorb=item.absorb or "d4")` → `self.state.player.armor = item` — item IS an Armor
- `roll(item.damage or "d6")` → `roll(item.heal)` for Potion

- [ ] **Step 5: Commit engine.py update**

```bash
git add src/dark_fort/game/engine.py
git commit -m "refactor: update engine.py to use item subclasses and isinstance matching"
```

---

### Task 5: Update widgets.py — import only (no logic change needed)

**Files:**
- Modify: `src/dark_fort/tui/widgets.py`

- [ ] **Step 1: Check widgets.py imports**

The current import on line 7 is `from dark_fort.game.models import Player`. This still works — `Player` is still exported from `models.py`. No changes needed to `widgets.py` since it only accesses `player.weapon.name`, `player.weapon.damage`, `player.armor.name`, `player.armor.absorb` — all still valid on the new `Weapon` and `Armor` subclasses.

**No code changes required for widgets.py.**

---

### Task 6: Update models.py `__init__.py` exports (if needed)

**Files:**
- Check: `src/dark_fort/game/__init__.py`

- [ ] **Step 1: Check and update __init__.py if it re-exports models**

Check if `src/dark_fort/game/__init__.py` re-exports model names. If it does, update to include `AnyItem`, `Potion`, `Scroll`, `Rope`, `Cloak` and remove `Item` (old flat class) and `armor_to_item`/`weapon_to_item`.

```bash
cat src/dark_fort/game/__init__.py
```

If no re-exports, skip this task.

---

### Task 7: Rewrite test_models.py — new subclass tests, remove conversion tests

**Files:**
- Modify: `tests/game/test_models.py`

- [ ] **Step 1: Rewrite test_models.py**

```python
import pytest
from pydantic import ValidationError

from dark_fort.game.enums import ItemType, MonsterTier, Phase, ScrollType
from dark_fort.game.models import (
    ActionResult,
    AnyItem,
    Armor,
    Cloak,
    CombatState,
    GameState,
    Item,
    Monster,
    Player,
    Potion,
    Room,
    Rope,
    Scroll,
    Weapon,
)


class TestWeapon:
    def test_create_weapon(self):
        weapon = Weapon(name="Warhammer", damage="d6")
        assert weapon.name == "Warhammer"
        assert weapon.damage == "d6"
        assert weapon.attack_bonus == 0
        assert weapon.type == ItemType.WEAPON

    def test_weapon_with_attack_bonus(self):
        weapon = Weapon(name="Sword", damage="d6", attack_bonus=1)
        assert weapon.attack_bonus == 1

    def test_weapon_is_item(self):
        weapon = Weapon(name="Dagger", damage="d4")
        assert isinstance(weapon, Item)


class TestArmor:
    def test_create_armor(self):
        armor = Armor(name="Armor", absorb="d4")
        assert armor.name == "Armor"
        assert armor.absorb == "d4"
        assert armor.type == ItemType.ARMOR

    def test_armor_default_absorb(self):
        armor = Armor(name="Armor")
        assert armor.absorb == "d4"

    def test_armor_is_item(self):
        armor = Armor(name="Chain Mail", absorb="d6")
        assert isinstance(armor, Item)


class TestPotion:
    def test_create_potion(self):
        potion = Potion(name="Potion", heal="d6")
        assert potion.name == "Potion"
        assert potion.heal == "d6"
        assert potion.type == ItemType.POTION

    def test_potion_is_item(self):
        potion = Potion(name="Potion", heal="d6")
        assert isinstance(potion, Item)


class TestScroll:
    def test_create_scroll(self):
        scroll = Scroll(name="Summon daemon", scroll_type=ScrollType.SUMMON_DAEMON)
        assert scroll.name == "Summon daemon"
        assert scroll.scroll_type == ScrollType.SUMMON_DAEMON
        assert scroll.type == ItemType.SCROLL

    def test_scroll_is_item(self):
        scroll = Scroll(name="Test scroll", scroll_type=ScrollType.FALSE_OMEN)
        assert isinstance(scroll, Item)


class TestRope:
    def test_create_rope(self):
        rope = Rope(name="Rope")
        assert rope.name == "Rope"
        assert rope.type == ItemType.ROPE

    def test_rope_is_item(self):
        rope = Rope(name="Rope")
        assert isinstance(rope, Item)


class TestCloak:
    def test_create_cloak(self):
        cloak = Cloak(name="Cloak of invisibility")
        assert cloak.name == "Cloak of invisibility"
        assert cloak.type == ItemType.CLOAK

    def test_cloak_is_item(self):
        cloak = Cloak(name="Cloak of invisibility")
        assert isinstance(cloak, Item)


class TestAnyItem:
    def test_anyitem_accepts_weapon(self):
        item: AnyItem = Weapon(name="Sword", damage="d6")
        assert isinstance(item, Weapon)

    def test_anyitem_accepts_armor(self):
        item: AnyItem = Armor(name="Armor", absorb="d4")
        assert isinstance(item, Armor)

    def test_anyitem_accepts_potion(self):
        item: AnyItem = Potion(name="Potion", heal="d6")
        assert isinstance(item, Potion)

    def test_anyitem_accepts_scroll(self):
        item: AnyItem = Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON)
        assert isinstance(item, Scroll)

    def test_anyitem_accepts_rope(self):
        item: AnyItem = Rope(name="Rope")
        assert isinstance(item, Rope)

    def test_anyitem_accepts_cloak(self):
        item: AnyItem = Cloak(name="Cloak of invisibility")
        assert isinstance(item, Cloak)


class TestMonster:
    def test_create_weak_monster(self):
        monster = Monster(
            name="Goblin",
            tier=MonsterTier.WEAK,
            points=3,
            damage="d4",
            hp=5,
            loot="Rope",
        )
        assert monster.tier == MonsterTier.WEAK
        assert monster.points == 3
        assert monster.hp == 5

    def test_create_tough_monster_with_special(self):
        monster = Monster(
            name="Medusa",
            tier=MonsterTier.TOUGH,
            points=4,
            damage="d6",
            hp=10,
            special="petrify_1_in_6",
        )
        assert monster.special == "petrify_1_in_6"


class TestPlayer:
    def test_default_player(self):
        player = Player()
        assert player.name == "Kargunt"
        assert player.hp == 15
        assert player.max_hp == 15
        assert player.silver == 0
        assert player.points == 0
        assert player.weapon is None
        assert player.armor is None
        assert player.inventory == []
        assert player.level_benefits == []

    def test_player_with_starting_silver(self):
        player = Player(silver=18)
        assert player.silver == 18

    def test_level_benefits_unique(self):
        with pytest.raises(ValidationError):
            Player(level_benefits=[1, 2, 2, 3])

    def test_player_inventory_accepts_mixed_items(self):
        player = Player()
        player.inventory.append(Weapon(name="Sword", damage="d6"))
        player.inventory.append(Potion(name="Potion", heal="d6"))
        player.inventory.append(Rope(name="Rope"))
        assert len(player.inventory) == 3

    def test_player_weapon_direct_assign(self):
        player = Player()
        player.weapon = Weapon(name="Sword", damage="d6")
        assert player.weapon.name == "Sword"
        assert player.weapon.damage == "d6"

    def test_player_weapon_to_inventory(self):
        player = Player()
        player.weapon = Weapon(name="Sword", damage="d6")
        player.inventory.append(player.weapon)
        assert len(player.inventory) == 1
        assert isinstance(player.inventory[0], Weapon)

    def test_player_armor_direct_assign(self):
        player = Player()
        player.armor = Armor(name="Armor", absorb="d4")
        assert player.armor.name == "Armor"
        assert player.armor.absorb == "d4"

    def test_player_armor_to_inventory(self):
        player = Player()
        player.armor = Armor(name="Armor", absorb="d4")
        player.inventory.append(player.armor)
        assert len(player.inventory) == 1
        assert isinstance(player.inventory[0], Armor)


class TestRoom:
    def test_create_room(self):
        room = Room(id=1, shape="Square", doors=2, result="nothing")
        assert room.explored is False
        assert room.connections == []

    def test_explored_room(self):
        room = Room(id=1, shape="Square", doors=2, result="nothing", explored=True)
        assert room.explored is True


class TestCombatState:
    def test_create_combat(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        combat = CombatState(monster=monster, monster_hp=5)
        assert combat.player_turns == 0
        assert combat.daemon_assist is False


class TestGameState:
    def test_default_game_state(self):
        state = GameState(phase=Phase.TITLE)
        assert state.phase == Phase.TITLE
        assert state.player is not None
        assert state.current_room is None
        assert state.rooms == {}
        assert state.combat is None
        assert state.level_up_queue is False
        assert state.log == []


class TestActionResult:
    def test_action_result_with_messages(self):
        result = ActionResult(messages=["You enter a room.", "A monster appears!"])
        assert len(result.messages) == 2

    def test_action_result_with_phase_change(self):
        result = ActionResult(messages=[], phase=Phase.COMBAT)
        assert result.phase == Phase.COMBAT

    def test_action_result_with_choices(self):
        from dark_fort.game.enums import Command

        result = ActionResult(messages=[], choices=[Command.ATTACK, Command.FLEE])
        assert len(result.choices) == 2
```

Key changes from current:
- Removed `TestConversionHelpers` (no more `weapon_to_item`/`armor_to_item`)
- Removed `TestItemAbsorb` (Armor has `absorb` as a required field, not optional on Item)
- Removed `TestItem.test_create_potion` and `TestItem.test_create_weapon_item` (old flat Item class)
- Added `TestPotion`, `TestScroll`, `TestRope`, `TestCloak`
- Added `TestAnyItem` for discriminated union validation
- Added `TestPlayer.test_player_inventory_accepts_mixed_items`, `test_player_weapon_to_inventory`, `test_player_armor_to_inventory`
- Removed import of `armor_to_item`, `weapon_to_item`
- Added imports for `AnyItem`, `Cloak`, `Potion`, `Rope`, `Scroll`, `ScrollType`

- [ ] **Step 2: Commit test_models.py rewrite**

```bash
git add tests/game/test_models.py
git commit -m "test: rewrite model tests for inheritance hierarchy"
```

---

### Task 8: Update test_engine.py — use subclass constructors

**Files:**
- Modify: `tests/game/test_engine.py`

- [ ] **Step 1: Update imports and test data in test_engine.py**

Replace line 2-3:
```python
from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import ItemType, Phase
from dark_fort.game.models import Armor, Item
```

with:
```python
from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Phase
from dark_fort.game.models import Armor, Potion, Weapon
```

- [ ] **Step 2: Update TestEquipWeapon tests**

```python
class TestEquipWeapon:
    def test_equip_weapon_from_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Weapon(name="Test Sword", damage="d6", attack_bonus=1)
        )
        engine.use_item(0)
        assert engine.state.player.weapon is not None
        assert engine.state.player.weapon.name == "Test Sword"
        assert all(item.name != "Test Sword" for item in engine.state.player.inventory)

    def test_equip_weapon_swaps_old_to_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        old_weapon = engine.state.player.weapon
        assert old_weapon is not None
        engine.state.player.inventory.append(
            Weapon(name="Sword", damage="d6", attack_bonus=1)
        )
        engine.use_item(0)
        assert engine.state.player.weapon is not None
        assert engine.state.player.weapon.name == "Sword"
        assert isinstance(engine.state.player.inventory[0], Weapon)
        assert engine.state.player.inventory[0].name == old_weapon.name

    def test_equip_weapon_when_none_equipped(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.weapon = None
        engine.state.player.inventory.append(
            Weapon(name="Dagger", damage="d4", attack_bonus=1)
        )
        engine.use_item(0)
        assert engine.state.player.weapon is not None
        assert engine.state.player.weapon.name == "Dagger"
```

- [ ] **Step 3: Update TestEquipArmor tests**

```python
class TestEquipArmor:
    def test_equip_armor_from_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Armor(name="Armor", absorb="d4")
        )
        engine.use_item(0)
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"

    def test_equip_armor_swaps_old_to_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.armor = Armor(name="Old Armor", absorb="d4")
        engine.state.player.inventory.append(
            Armor(name="New Armor", absorb="d6")
        )
        engine.use_item(0)
        assert engine.state.player.armor.name == "New Armor"
        old_in_inventory = any(
            item.name == "Old Armor" for item in engine.state.player.inventory
        )
        assert old_in_inventory

    def test_equip_armor_when_none_equipped(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.armor = None
        engine.state.player.inventory.append(
            Armor(name="Armor", absorb="d4")
        )
        engine.use_item(0)
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"
```

- [ ] **Step 4: Update TestBuyArmor tests**

```python
class TestBuyArmor:
    def test_buy_armor_equips_it(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.armor = None
        engine.state.player.silver = 20
        engine.state.phase = Phase.SHOP
        engine.buy_item(8)  # Armor is index 8
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"
        assert engine.state.player.armor.absorb == "d4"

    def test_buy_armor_swaps_existing(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.armor = Armor(name="Old Armor", absorb="d4")
        engine.state.player.silver = 20
        engine.state.phase = Phase.SHOP
        engine.buy_item(8)  # Armor is index 8
        assert engine.state.player.armor.name == "Armor"
        assert any(item.name == "Old Armor" for item in engine.state.player.inventory)
```

- [ ] **Step 5: Update TestEquipSwapIntegration tests**

```python
class TestEquipSwapIntegration:
    def test_full_weapon_swap_flow(self):
        engine = GameEngine()
        engine.start_game()
        old_weapon_name = engine.state.player.weapon.name  # ty: ignore[unresolved-attribute]
        engine.state.player.inventory.append(
            Weapon(name="Flail", damage="d6+1")
        )
        engine.use_item(0)
        assert engine.state.player.weapon.name == "Flail"  # ty: ignore[unresolved-attribute]
        assert any(
            item.name == old_weapon_name for item in engine.state.player.inventory
        )

    def test_full_armor_swap_flow(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.armor = Armor(name="Armor", absorb="d4")
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Armor(name="Chain Mail", absorb="d6")
        )
        engine.use_item(0)
        assert engine.state.player.armor.name == "Chain Mail"
        assert any(item.name == "Armor" for item in engine.state.player.inventory)

    def test_buy_armor_then_equip_another(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 30
        engine.state.phase = Phase.SHOP
        engine.buy_item(8)  # Buy Armor
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"
```

- [ ] **Step 6: Commit test_engine.py update**

```bash
git add tests/game/test_engine.py
git commit -m "test: update engine tests for item subclasses"
```

---

### Task 9: Update test_rules.py — use subclass constructors

**Files:**
- Modify: `tests/game/test_rules.py`

- [ ] **Step 1: Update imports and test data**

Replace lines 1-21:
```python
from dark_fort.game.enums import ItemType, MonsterTier, Phase
from dark_fort.game.models import (
    Armor,
    CombatState,
    GameState,
    Monster,
    Player,
    Potion,
    Rope,
    Weapon,
)
from dark_fort.game.rules import (
    apply_level_benefit,
    check_level_up,
    flee_combat,
    generate_starting_equipment,
    has_rope,
    resolve_combat_hit,
    resolve_monster_special,
    resolve_pit_trap,
)
```

Changes: Removed `Item`, added `Potion`, `Rope`.

- [ ] **Step 2: Update TestLevelBenefits**

Replace `test_benefit_4_gives_5_potions`:
```python
    def test_benefit_4_gives_5_potions(self):
        player = Player(inventory=[])
        apply_level_benefit(4, player)
        potions = [i for i in player.inventory if isinstance(i, Potion)]
        assert len(potions) == 5
```

Replace `test_benefit_5_gives_zweihander`:
```python
    def test_benefit_5_gives_zweihander(self):
        player = Player()
        apply_level_benefit(5, player)
        assert any(isinstance(w, Weapon) and w.name == "Mighty Zweihänder" for w in player.inventory)
```

- [ ] **Step 3: Update TestPitTrap**

Replace `test_pit_trap_with_rope_gets_bonus`:
```python
    def test_pit_trap_with_rope_gets_bonus(self):
        player = Player()
        player.inventory.append(Rope(name="Rope"))
        resolve_pit_trap(player, dice_roll=4)
        assert player.hp == 15
```

- [ ] **Step 4: Update TestStartingEquipmentArmor**

Replace `test_starting_armor_item_has_absorb`:
```python
    def test_starting_armor_item_has_absorb(self):
        weapon, item = generate_starting_equipment()
        if isinstance(item, Armor):
            assert item.absorb == "d4"
```

- [ ] **Step 5: Update TestHasRope**

```python
class TestHasRope:
    def test_has_rope_returns_true(self):
        player = Player()
        player.inventory.append(Rope(name="Rope"))
        assert has_rope(player) is True

    def test_has_rope_returns_false(self):
        player = Player()
        assert has_rope(player) is False
```

- [ ] **Step 6: Commit test_rules.py update**

```bash
git add tests/game/test_rules.py
git commit -m "test: update rules tests for item subclasses"
```

---

### Task 10: Update test_tables.py — use subclass assertions

**Files:**
- Modify: `tests/game/test_tables.py`

- [ ] **Step 1: Update TestShopItemsArmor**

```python
class TestShopItemsArmor:
    def test_armor_shop_item_is_armor(self):
        from dark_fort.game.models import Armor

        armor_items = [
            (item, price) for item, price in SHOP_ITEMS if isinstance(item, Armor)
        ]
        assert len(armor_items) >= 1
        armor_item, price = armor_items[0]
        assert armor_item.absorb == "d4"
        assert price == 10
```

- [ ] **Step 2: Commit test_tables.py update**

```bash
git add tests/game/test_tables.py
git commit -m "test: update tables tests for item subclasses"
```

---

### Task 11: Update test_widgets.py — import changes

**Files:**
- Modify: `tests/tui/test_widgets.py`

- [ ] **Step 1: Update import line**

Line 5 currently:
```python
from dark_fort.game.models import Armor, Player, Weapon
```
No change needed — `Armor`, `Player`, `Weapon` are still exported from models.py.

The test code creates `Weapon(name="Warhammer", damage="d6")` and `Armor(name="Armor", absorb="d4")` — these constructors still work with the new hierarchy. `Weapon` and `Armor` just gain a `type` default. **No changes required.**

---

### Task 12: Run full test suite and lint

- [ ] **Step 1: Run `make test`**

```bash
make test
```

Expected: All tests pass.

- [ ] **Step 2: Run `make lint`**

```bash
make lint
```

Expected: No lint or type errors.

- [ ] **Step 3: If tests or lint fail, fix and re-run**

Common issues to watch for:
- `from dark_fort.game.models import Item` — any remaining imports of the old flat `Item` class need updating
- `item.type == ItemType.X` checks in engine.py or rules.py that should use `isinstance`
- `item.damage` on a Potion (now `item.heal`)
- `item.absorb` on an Item that should be an Armor
- Any test that constructs `Item(name=..., type=ItemType.WEAPON, damage=...)` etc.

- [ ] **Step 4: Final commit if fixes were needed**

```bash
git add -A
git commit -m "fix: resolve test and lint issues from model refactor"
```