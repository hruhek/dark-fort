import pytest
from pydantic import ValidationError

from dark_fort.game.enums import (
    EquipSlot,
    MonsterSpecial,
    MonsterTier,
    Phase,
    ScrollType,
)
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    CombatState,
    GameState,
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

    def test_weapon_with_attack_bonus(self):
        weapon = Weapon(name="Sword", damage="d6", attack_bonus=1)
        assert weapon.attack_bonus == 1


class TestPotion:
    def test_create_potion(self):
        potion = Potion(name="Potion", heal="d6")
        assert potion.heal == "d6"


class TestScroll:
    def test_create_scroll(self):
        scroll = Scroll(name="Scroll of Fire", scroll_type=ScrollType.SUMMON_DAEMON)
        assert scroll.scroll_type == ScrollType.SUMMON_DAEMON


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
            special=MonsterSpecial.PETRIFY,
        )
        assert monster.special == MonsterSpecial.PETRIFY


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

    def test_equip_weapon(self):
        player = Player()
        old_weapon = Weapon(name="Dagger", damage="d4")
        new_weapon = Weapon(name="Sword", damage="d6")
        player.weapon = old_weapon
        player.inventory = [new_weapon]

        messages = player.equip(new_weapon, 0)

        assert player.weapon == new_weapon
        assert old_weapon in player.inventory
        assert "Sword" in messages[1]
        assert len(player.inventory) == 1

    def test_equip_armor(self):
        player = Player()
        old_armor = Armor(name="Leather", absorb="d4")
        new_armor = Armor(name="Chain", absorb="d6")
        player.armor = old_armor
        player.inventory = [new_armor]

        messages = player.equip(new_armor, 0)

        assert player.armor == new_armor
        assert old_armor in player.inventory
        assert "Chain" in messages[1]
        assert len(player.inventory) == 1


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
        assert state.shop_wares == []
        assert state.log == []

    def test_game_state_snapshot_and_restore(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.silver = 42
        data = state.snapshot()
        restored = GameState.restore(data)
        assert restored.phase == Phase.EXPLORING
        assert restored.player.silver == 42


class TestActionResult:
    def test_action_result_with_messages(self):
        result = ActionResult(messages=["You enter a room.", "A monster appears!"])
        assert len(result.messages) == 2

    def test_action_result_with_phase_change(self):
        result = ActionResult(messages=[], phase=Phase.COMBAT)
        assert result.phase == Phase.COMBAT


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


class TestInventory:
    def test_inventory_with_weapon(self):
        player = Player()
        player.inventory = [Weapon(name="Sword", damage="d6")]
        assert isinstance(player.inventory[0], Weapon)

    def test_inventory_with_armor(self):
        player = Player()
        player.inventory = [Armor(name="Armor", absorb="d4")]
        assert isinstance(player.inventory[0], Armor)

    def test_inventory_with_potion(self):
        player = Player()
        player.inventory = [Potion(name="Potion", heal="d6")]
        assert isinstance(player.inventory[0], Potion)

    def test_inventory_with_scroll(self):
        player = Player()
        player.inventory = [Scroll(name="Scroll", scroll_type=ScrollType.SOUTHERN_GATE)]
        assert isinstance(player.inventory[0], Scroll)

    def test_inventory_with_cloak(self):
        player = Player()
        player.inventory = [Cloak(name="Cloak")]
        assert isinstance(player.inventory[0], Cloak)


class TestEquipSlot:
    def test_weapon_equip_slot(self):
        weapon = Weapon(name="Sword", damage="d6")
        assert weapon.equip_slot == EquipSlot.WEAPON

    def test_armor_equip_slot(self):
        armor = Armor(name="Armor", absorb="d4")
        assert armor.equip_slot == EquipSlot.ARMOR

    def test_potion_equip_slot(self):
        potion = Potion(name="Potion", heal="d6")
        assert potion.equip_slot == EquipSlot.NONE

    def test_scroll_equip_slot(self):
        scroll = Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON)
        assert scroll.equip_slot == EquipSlot.NONE

    def test_rope_equip_slot(self):
        rope = Rope(name="Rope")
        assert rope.equip_slot == EquipSlot.NONE

    def test_cloak_equip_slot(self):
        cloak = Cloak(name="Cloak")
        assert cloak.equip_slot == EquipSlot.SPECIAL
