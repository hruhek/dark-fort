from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from dark_fort.game.dice import roll
from dark_fort.game.enums import (
    EquipSlot,
    ItemType,
    MonsterSpecial,
    MonsterTier,
    Phase,
    ScrollType,
)


# BaseModel enables: discriminated unions (AnyItem), model_dump/model_validate
# for save/load serialization, and runtime validation on deserialization.
class Item(BaseModel):
    name: str
    equip_slot: EquipSlot = EquipSlot.NONE

    def use(self, state: GameState, index: int) -> ActionResult:
        raise NotImplementedError(f"use() not implemented for {type(self).__name__}")

    def display_stats(self) -> str:
        return ""


class Weapon(Item):
    type: Literal[ItemType.WEAPON] = ItemType.WEAPON
    equip_slot: EquipSlot = EquipSlot.WEAPON
    damage: str
    attack_bonus: int = 0

    def display_stats(self) -> str:
        stats = self.damage
        if self.attack_bonus:
            stats += f"/+{self.attack_bonus}"
        return stats

    def use(self, state: GameState, index: int) -> ActionResult:
        messages = state.player.equip(self, index)
        return ActionResult(messages=messages)


class Armor(Item):
    type: Literal[ItemType.ARMOR] = ItemType.ARMOR
    equip_slot: EquipSlot = EquipSlot.ARMOR
    absorb: str = "d4"

    def display_stats(self) -> str:
        return self.absorb

    def use(self, state: GameState, index: int) -> ActionResult:
        messages = state.player.equip(self, index)
        return ActionResult(messages=messages)


class Potion(Item):
    type: Literal[ItemType.POTION] = ItemType.POTION
    equip_slot: EquipSlot = EquipSlot.NONE
    heal: str

    def display_stats(self) -> str:
        return f"heal {self.heal}"

    def use(self, state: GameState, index: int) -> ActionResult:
        messages: list[str] = []
        player = state.player
        heal = roll(self.heal)
        player.hp = min(player.hp + heal, player.max_hp)
        messages.append(f"You drink the potion and heal {heal} HP.")
        player.inventory.pop(index)
        return ActionResult(messages=messages)


class Scroll(Item):
    type: Literal[ItemType.SCROLL] = ItemType.SCROLL
    equip_slot: EquipSlot = EquipSlot.NONE
    scroll_type: ScrollType

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        messages = [f"You unroll the {self.name}... (effect not yet implemented)"]
        state.player.inventory.pop(index)
        return ActionResult(messages=messages)


class Rope(Item):
    type: Literal[ItemType.ROPE] = ItemType.ROPE
    equip_slot: EquipSlot = EquipSlot.NONE

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        return ActionResult(messages=[])


class Cloak(Item):
    type: Literal[ItemType.CLOAK] = ItemType.CLOAK
    equip_slot: EquipSlot = EquipSlot.SPECIAL
    charges: int = 0

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        self.charges = max(0, self.charges - 1)
        return ActionResult(
            messages=[f"Cloak activated. {self.charges} charges remaining."]
        )


AnyItem = Annotated[
    Weapon | Armor | Potion | Scroll | Rope | Cloak,
    Field(discriminator="type"),
]


class ShopEntry(BaseModel):
    item: AnyItem
    price: int

    def display_stats(self) -> str:
        stats = self.item.display_stats()
        stats_str = f" ({stats})" if stats else ""
        return f"{self.item.name}{stats_str} — {self.price}s"


class Monster(BaseModel):
    name: str
    tier: MonsterTier
    points: int
    damage: str
    hp: int
    loot: str | None = None
    special: MonsterSpecial | None = None


class Player(BaseModel):
    name: str = "Kargunt"
    hp: int = 15
    max_hp: int = 15
    silver: int = 0
    points: int = 0
    weapon: Weapon | None = None
    armor: Armor | None = None
    inventory: list[AnyItem] = Field(default_factory=list)
    attack_bonus: int = 0
    level_benefits: list[int] = Field(default_factory=list)
    daemon_fights_remaining: int = 0

    @field_validator("level_benefits")
    @classmethod
    def level_benefits_must_be_unique(cls, v: list[int]) -> list[int]:
        if len(v) != len(set(v)):
            raise ValueError("level_benefits must contain unique values")
        return v

    def equip(self, item: Weapon | Armor, index: int) -> list[str]:
        slot_attr = "weapon" if isinstance(item, Weapon) else "armor"
        messages: list[str] = []
        current = getattr(self, slot_attr)
        if current is not None:
            self.inventory.append(current)
            messages.append(f"{current.name} moved to inventory.")
        setattr(self, slot_attr, item)
        messages.append(f"You equip the {item.name}.")
        self.inventory.pop(index)
        return messages


class Exit(BaseModel):
    door_number: int
    destination: int
    direction: str


class Room(BaseModel):
    id: int
    shape: str
    result: str
    explored: bool = False
    exits: list[Exit] = Field(default_factory=list)


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
    shop_wares: list[ShopEntry] = Field(default_factory=list)
    log: list[str] = Field(default_factory=list)

    def snapshot(self) -> dict:
        return self.model_dump()

    @classmethod
    def restore(cls, data: dict) -> GameState:
        return cls.model_validate(data)


class ActionResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None


class RoomEventResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
    combat: CombatState | None = None
    explored: bool = False
    silver_delta: int = 0
    hp_delta: int = 0
