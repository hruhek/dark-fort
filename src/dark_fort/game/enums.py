from enum import StrEnum, auto


class ItemType(StrEnum):
    WEAPON = auto()
    ARMOR = auto()
    POTION = auto()
    SCROLL = auto()
    ROPE = auto()
    CLOAK = auto()


class MonsterTier(StrEnum):
    WEAK = auto()
    TOUGH = auto()


class Phase(StrEnum):
    TITLE = auto()
    ENTRANCE = auto()
    EXPLORING = auto()
    COMBAT = auto()
    SHOP = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Command(StrEnum):
    ATTACK = auto()
    FLEE = auto()
    USE_ITEM = auto()
    EXPLORE = auto()
    INVENTORY = auto()
    MOVE = auto()
    BROWSE = auto()
    LEAVE = auto()
    BUY = auto()


class ScrollType(StrEnum):
    SUMMON_DAEMON = auto()
    SOUTHERN_GATE = auto()
    AEGIS_OF_SORROW = auto()
    FALSE_OMEN = auto()


class RoomEvent(StrEnum):
    EMPTY = auto()
    PIT_TRAP = auto()
    SOOTHSAYER = auto()
    WEAK_MONSTER = auto()
    TOUGH_MONSTER = auto()
    SHOP = auto()


class MonsterSpecial(StrEnum):
    LOOT_DAGGER = auto()
    LOOT_SCROLL = auto()
    LOOT_ROPE = auto()
    DEATH_RAY = auto()
    PETRIFY = auto()
    INSTANT_LEVEL_UP = auto()
    SEVEN_POINTS_ON_KILL = auto()


class ActionKind(StrEnum):
    INVENTORY = auto()
    COMBAT = auto()
    SHOP = auto()
    ROOM = auto()
    NAVIGATION = auto()
    LEVEL_UP = auto()


class EquipSlot(StrEnum):
    WEAPON = auto()
    ARMOR = auto()
    NONE = auto()
    SPECIAL = auto()
