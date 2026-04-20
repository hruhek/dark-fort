from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator

from dark_fort.game.enums import Command, ItemType, MonsterTier, Phase


class Weapon(BaseModel):
    name: str
    damage: str
    attack_bonus: int = 0


class Armor(BaseModel):
    name: str
    absorb: str = "d4"


class Item(BaseModel):
    name: str
    type: ItemType
    damage: str | None = None
    attack_bonus: int = 0
    absorb: str | None = None
    uses: int | None = None


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
    armor: bool = False
    inventory: list[Item] = []
    scrolls: list[Item] = []
    cloak_charges: int = 0
    attack_bonus: int = 0
    level_benefits: list[int] = []
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
    connections: list[int] = []


class CombatState(BaseModel):
    monster: Monster
    monster_hp: int
    player_turns: int = 0
    daemon_assist: bool = False


class GameState(BaseModel):
    player: Player = Player()
    current_room: Room | None = None
    rooms: dict[int, Room] = {}
    phase: Phase
    combat: CombatState | None = None
    level_up_queue: bool = False
    log: list[str] = []


class ActionResult(BaseModel):
    messages: list[str]
    phase: Phase | None = None
    choices: list[Command] = []
    state_delta: dict[str, Any] = {}
