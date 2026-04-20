from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import ItemType, Phase
from dark_fort.game.models import Armor, Item


class TestGameEngine:
    def test_new_engine_has_title_phase(self):
        engine = GameEngine()
        assert engine.state.phase == "title"

    def test_start_game_generates_entrance(self):
        engine = GameEngine()
        result = engine.start_game()
        assert engine.state.phase == "exploring"
        assert engine.state.current_room is not None
        assert result.messages

    def test_enter_new_room_generates_room(self):
        engine = GameEngine()
        engine.start_game()
        result = engine.enter_new_room()
        assert engine.state.current_room is not None
        assert result.messages

    def test_shop_purchase_deducts_silver(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 20
        engine.state.phase = Phase.SHOP

        result = engine.buy_item(0)
        assert engine.state.player.silver == 16
        assert result.messages

    def test_shop_purchase_fails_without_silver(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 1
        engine.state.phase = Phase.SHOP

        result = engine.buy_item(7)
        assert any("not enough" in m.lower() for m in result.messages)

    def test_leave_shop_returns_to_exploring(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.phase = Phase.SHOP

        engine.leave_shop()
        assert engine.state.phase == "exploring"

    def test_count_explored_rooms(self):
        from dark_fort.game.models import Room

        engine = GameEngine()
        engine.start_game()
        for i in range(5):
            engine.state.rooms[i] = Room(
                id=i, shape="Square", doors=1, result="nothing", explored=True
            )
        assert engine.explored_count == 5

    def test_victory_when_all_benefits_claimed(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]
        engine.check_victory()
        assert engine.state.phase == Phase.VICTORY


class TestEquipWeapon:
    def test_equip_weapon_from_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Item(name="Test Sword", type=ItemType.WEAPON, damage="d6", attack_bonus=1)
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
            Item(name="Sword", type=ItemType.WEAPON, damage="d6", attack_bonus=1)
        )
        engine.use_item(0)
        assert engine.state.player.weapon is not None
        assert engine.state.player.weapon.name == "Sword"
        assert any(
            item.name == old_weapon.name for item in engine.state.player.inventory
        )

    def test_equip_weapon_when_none_equipped(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.weapon = None
        engine.state.player.inventory.append(
            Item(name="Dagger", type=ItemType.WEAPON, damage="d4", attack_bonus=1)
        )
        engine.use_item(0)
        assert engine.state.player.weapon is not None
        assert engine.state.player.weapon.name == "Dagger"


class TestEquipArmor:
    def test_equip_armor_from_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Item(name="Armor", type=ItemType.ARMOR, absorb="d4")
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
            Item(name="New Armor", type=ItemType.ARMOR, absorb="d6")
        )
        engine.use_item(0)
        assert engine.state.player.armor.name == "New Armor"
        assert any(item.name == "Old Armor" for item in engine.state.player.inventory)

    def test_equip_armor_when_none_equipped(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.armor = None
        engine.state.player.inventory.append(
            Item(name="Armor", type=ItemType.ARMOR, absorb="d4")
        )
        engine.use_item(0)
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"


class TestBuyArmor:
    def test_buy_armor_equips_it(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.armor = None  # Ensure no armor equipped
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
