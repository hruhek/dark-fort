from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, field_validator

from dark_fort.game.dice import roll
from dark_fort.game.enums import (
    Command,
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

    def use(self, state: GameState, index: int) -> ActionResult:
        raise NotImplementedError(f"use() not implemented for {type(self).__name__}")

    def display_stats(self) -> str:
        return ""


class Weapon(Item):
    type: Literal[ItemType.WEAPON] = ItemType.WEAPON
    damage: str
    attack_bonus: int = 0

    def display_stats(self) -> str:
        stats = self.damage
        if self.attack_bonus:
            stats += f"/+{self.attack_bonus}"
        return stats

    def use(self, state: GameState, index: int) -> ActionResult:
        messages: list[str] = []
        player = state.player
        if player.weapon is not None:
            player.inventory.append(player.weapon)
            messages.append(f"{player.weapon.name} moved to inventory.")
        player.weapon = self
        messages.append(f"You equip the {self.name}.")
        player.inventory.pop(index)
        return ActionResult(messages=messages)


class Armor(Item):
    type: Literal[ItemType.ARMOR] = ItemType.ARMOR
    absorb: str = "d4"

    def display_stats(self) -> str:
        return self.absorb

    def use(self, state: GameState, index: int) -> ActionResult:
        messages: list[str] = []
        player = state.player
        if player.armor is not None:
            player.inventory.append(player.armor)
            messages.append(f"{player.armor.name} moved to inventory.")
        player.armor = self
        messages.append(f"You equip the {self.name}.")
        player.inventory.pop(index)
        return ActionResult(messages=messages)


class Potion(Item):
    type: Literal[ItemType.POTION] = ItemType.POTION
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
    scroll_type: ScrollType

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        messages = [f"You unroll the {self.name}..."]
        state.player.inventory.pop(index)
        return ActionResult(messages=messages)


class Rope(Item):
    type: Literal[ItemType.ROPE] = ItemType.ROPE

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        return ActionResult(messages=[])


class Cloak(Item):
    type: Literal[ItemType.CLOAK] = ItemType.CLOAK

    def display_stats(self) -> str:
        return ""

    def use(self, state: GameState, index: int) -> ActionResult:
        player = state.player
        player.cloak_charges = max(0, player.cloak_charges - 1)
        return ActionResult(
            messages=[f"Cloak activated. {player.cloak_charges} charges remaining."]
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
