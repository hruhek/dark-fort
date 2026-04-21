from dark_fort.game.enums import MonsterSpecial, MonsterTier, RoomEvent, ScrollType
from dark_fort.game.models import (
    AnyItem,
    Armor,
    Cloak,
    Monster,
    Potion,
    Rope,
    Scroll,
    Weapon,
)

# ---------------------------------------------------------------------------
# Monster tables
# ---------------------------------------------------------------------------

WEAK_MONSTERS: list[Monster] = [
    Monster(
        name="Blood-Drenched Skeleton",
        tier=MonsterTier.WEAK,
        points=3,
        damage="d4",
        hp=6,
        loot="Dagger",
        special=MonsterSpecial.LOOT_DAGGER,
    ),
    Monster(
        name="Catacomb Cultist",
        tier=MonsterTier.WEAK,
        points=3,
        damage="d4",
        hp=6,
        loot="Random scroll",
        special=MonsterSpecial.LOOT_SCROLL,
    ),
    Monster(
        name="Goblin",
        tier=MonsterTier.WEAK,
        points=3,
        damage="d4",
        hp=5,
        loot="Rope",
        special=MonsterSpecial.LOOT_ROPE,
    ),
    Monster(
        name="Undead Hound",
        tier=MonsterTier.WEAK,
        points=4,
        damage="d4",
        hp=6,
    ),
]

TOUGH_MONSTERS: list[Monster] = [
    Monster(
        name="Necro-Sorcerer",
        tier=MonsterTier.TOUGH,
        points=4,
        damage="d4",
        hp=8,
        loot="3d6 silver",
        special=MonsterSpecial.DEATH_RAY,
    ),
    Monster(
        name="Small Stone Troll",
        tier=MonsterTier.TOUGH,
        points=5,
        damage="d6+1",
        hp=9,
        special=MonsterSpecial.SEVEN_POINTS_ON_KILL,
    ),
    Monster(
        name="Medusa",
        tier=MonsterTier.TOUGH,
        points=4,
        damage="d6",
        hp=10,
        loot="d4×d6 silver",
        special=MonsterSpecial.PETRIFY,
    ),
    Monster(
        name="Ruin Basilisk",
        tier=MonsterTier.TOUGH,
        points=4,
        damage="d6",
        hp=11,
        special=MonsterSpecial.INSTANT_LEVEL_UP,
    ),
]

# ---------------------------------------------------------------------------
# Shop table — (Item, price) pairs
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Room shapes — indexed by 2d6 result minus 2 (i.e. index 0 = roll of 2)
# ---------------------------------------------------------------------------

ROOM_SHAPES: list[str] = [
    "Irregular cave",  # 2
    "Oval",  # 3
    "Cross-shaped",  # 4
    "Corridor",  # 5
    "Square",  # 6
    "Square",  # 7
    "Square",  # 8
    "Round",  # 9
    "Rectangular",  # 10
    "Triangular",  # 11
    "Skull-shaped",  # 12
]

# ---------------------------------------------------------------------------
# Room result table — indexed by d6 minus 1
# ---------------------------------------------------------------------------

ROOM_RESULTS: list[RoomEvent] = [
    RoomEvent.EMPTY,
    RoomEvent.PIT_TRAP,
    RoomEvent.SOOTHSAYER,
    RoomEvent.WEAK_MONSTER,
    RoomEvent.TOUGH_MONSTER,
    RoomEvent.SHOP,
]

# ---------------------------------------------------------------------------
# Entrance room table — indexed by d4 minus 1
# ---------------------------------------------------------------------------

ENTRANCE_RESULTS: list[str] = [
    "Find a random item",
    "A weak monster stands guard",
    "A dying mystic gives a random scroll",
    "The entrance is eerily quiet",
]

# ---------------------------------------------------------------------------
# Items table — indexed by d6 minus 1
# ---------------------------------------------------------------------------

ITEMS_TABLE: list[str] = [
    "Random weapon",
    "Potion",
    "Rope",
    "Random scroll",
    "Armor",
    "Cloak of invisibility",
]

# ---------------------------------------------------------------------------
# Scrolls table — indexed by d4 minus 1
# ---------------------------------------------------------------------------

SCROLLS_TABLE: list[tuple[str, ScrollType, str]] = [
    (
        "Summon weak daemon",
        ScrollType.SUMMON_DAEMON,
        "The daemon helps you d4 fights, dealing d4 damage",
    ),
    ("Palms Open the Southern Gate", ScrollType.SOUTHERN_GATE, "d6+1 damage, d4 uses"),
    ("Aegis of Sorrow", ScrollType.AEGIS_OF_SORROW, "-d4 damage, d4 uses"),
    ("False Omen", ScrollType.FALSE_OMEN, "Choose Room result OR reroll any die"),
]

# ---------------------------------------------------------------------------
# Starting weapons table — indexed by d4 minus 1
# ---------------------------------------------------------------------------

WEAPONS_TABLE: list[Weapon] = [
    Weapon(name="Warhammer", damage="d6"),
    Weapon(name="Dagger", damage="d4", attack_bonus=1),
    Weapon(name="Sword", damage="d6", attack_bonus=1),
    Weapon(name="Flail", damage="d6+1"),
]

# ---------------------------------------------------------------------------
# Armor table
# ---------------------------------------------------------------------------

ARMOR_TABLE: list[Armor] = [
    Armor(name="Armor", absorb="d4"),
]

# ---------------------------------------------------------------------------
# Level benefits — indexed by d6 minus 1
# ---------------------------------------------------------------------------

LEVEL_BENEFITS: list[str] = [
    "Knighted (Sir/Lady Kargunt)",
    "+1 attack permanently",
    "Max HP becomes 20",
    "Gain 5 potions",
    "Gain Mighty Zweihänder",
    "Choose 1 Weak + 1 Tough monster; their damage is halved permanently",
]

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_weak_monster(index: int) -> Monster:
    return WEAK_MONSTERS[index % len(WEAK_MONSTERS)]


def get_tough_monster(index: int) -> Monster:
    return TOUGH_MONSTERS[index % len(TOUGH_MONSTERS)]


def get_shop_item(index: int) -> tuple[AnyItem, int]:
    return SHOP_ITEMS[index % len(SHOP_ITEMS)]


def get_room_shape(roll_2d6: int) -> str:
    """Get room shape from a 2d6 roll (2-12)."""
    idx = max(0, min(roll_2d6 - 2, len(ROOM_SHAPES) - 1))
    return ROOM_SHAPES[idx]
