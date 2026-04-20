import pytest
from pydantic import ValidationError

from dark_fort.game.enums import ItemType, MonsterTier, Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    CombatState,
    GameState,
    Item,
    Monster,
    Player,
    Room,
    Weapon,
    armor_to_item,
    weapon_to_item,
)


class TestWeapon:
    def test_create_weapon(self):
        weapon = Weapon(name="Warhammer", damage="d6")
        assert weapon.name == "Warhammer"
        assert weapon.damage == "d6"
        assert weapon.attack_bonus == 0

    def test_weapon_with_attack_bonus(self):
        weapon = Weapon(name="Sword", damage="d6", attack_bonus=1)
        assert weapon.attack_bonus == 1


class TestItem:
    def test_create_potion(self):
        item = Item(name="Potion", type=ItemType.POTION)
        assert item.type == ItemType.POTION
        assert item.damage is None

    def test_create_weapon_item(self):
        item = Item(name="Dagger", type=ItemType.WEAPON, damage="d4", attack_bonus=1)
        assert item.damage == "d4"
        assert item.attack_bonus == 1


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


class TestArmor:
    def test_create_armor(self):
        armor = Armor(name="Armor", absorb="d4")
        assert armor.name == "Armor"
        assert armor.absorb == "d4"

    def test_armor_default_absorb(self):
        armor = Armor(name="Armor")
        assert armor.absorb == "d4"


class TestPlayerArmor:
    def test_player_armor_defaults_none(self):
        player = Player()
        assert player.armor is None

    def test_player_can_equip_armor(self):
        player = Player()
        player.armor = Armor(name="Armor", absorb="d4")
        assert player.armor is not None
        assert player.armor.name == "Armor"
        assert player.armor.absorb == "d4"


class TestItemAbsorb:
    def test_create_armor_item_with_absorb(self):
        item = Item(name="Armor", type=ItemType.ARMOR, absorb="d4")
        assert item.absorb == "d4"

    def test_item_absorb_defaults_none(self):
        item = Item(name="Potion", type=ItemType.POTION)
        assert item.absorb is None


class TestConversionHelpers:
    def test_weapon_to_item(self):
        weapon = Weapon(name="Sword", damage="d6", attack_bonus=1)
        item = weapon_to_item(weapon)
        assert item.name == "Sword"
        assert item.type == ItemType.WEAPON
        assert item.damage == "d6"
        assert item.attack_bonus == 1

    def test_armor_to_item(self):
        armor = Armor(name="Armor", absorb="d4")
        item = armor_to_item(armor)
        assert item.name == "Armor"
        assert item.type == ItemType.ARMOR
        assert item.absorb == "d4"

    def test_weapon_to_item_preserves_all_fields(self):
        weapon = Weapon(name="Flail", damage="d6+1")
        item = weapon_to_item(weapon)
        assert item.attack_bonus == 0
        assert item.damage == "d6+1"
