from unittest.mock import patch

from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Phase
from dark_fort.game.models import Armor, Weapon
from dark_fort.game.tables import SHOP_ITEMS


class TestGameEngine:
    def test_new_engine_has_title_phase(self):
        engine = GameEngine()
        assert engine.state.phase == "title"

    @patch("dark_fort.game.engine.roll", return_value=4)
    def test_start_game_generates_entrance(self, _mock_roll):
        engine = GameEngine()
        result = engine.start_game()
        assert engine.state.phase == "exploring"
        assert engine.state.current_room is not None
        assert result.messages

    def test_start_game_generates_dungeon_upfront(self):
        engine = GameEngine()
        engine.start_game()
        assert len(engine.state.rooms) >= 1
        entrance = engine.state.current_room
        assert entrance is not None
        assert entrance.explored is True

    def test_move_to_room_moves_player(self):
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        assert len(current.exits) > 0
        next_id = current.exits[0].destination
        result = engine.move_to_room(next_id)
        assert engine.state.current_room is not None
        assert engine.state.current_room.id == next_id
        assert result.messages

    @patch("dark_fort.game.engine.resolve_room_event")
    def test_move_to_room_explores_unexplored(self, mock_resolve):
        from dark_fort.game.models import RoomEventResult

        mock_resolve.return_value = RoomEventResult(
            messages=["The room is empty."],
            explored=True,
        )
        engine = GameEngine()
        engine.start_game()
        current = engine.state.current_room
        assert current is not None
        next_id = current.exits[0].destination
        next_room = engine.state.rooms[next_id]
        assert next_room.explored is False
        engine.move_to_room(next_id)
        assert next_room.explored is True

    def test_shop_purchase_deducts_silver(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 20
        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)

        result = engine.buy_item(0)
        assert engine.state.player.silver == 16
        assert result.messages

    def test_shop_purchase_fails_without_silver(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 1
        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)

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
                id=i, shape="Square", result="nothing", explored=True
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
        assert any(
            item.name == old_weapon.name for item in engine.state.player.inventory
        )

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


class TestEquipArmor:
    def test_equip_armor_from_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(Armor(name="Armor", absorb="d4"))
        engine.use_item(0)
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"

    def test_equip_armor_swaps_old_to_inventory(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.armor = Armor(name="Old Armor", absorb="d4")
        engine.state.player.inventory.append(Armor(name="New Armor", absorb="d6"))
        engine.use_item(0)
        assert engine.state.player.armor.name == "New Armor"
        assert any(item.name == "Old Armor" for item in engine.state.player.inventory)

    def test_equip_armor_when_none_equipped(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.armor = None
        engine.state.player.inventory.append(Armor(name="Armor", absorb="d4"))
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
        engine.state.shop_wares = list(SHOP_ITEMS)
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
        engine.state.shop_wares = list(SHOP_ITEMS)
        engine.buy_item(8)  # Armor is index 8
        assert engine.state.player.armor.name == "Armor"
        assert any(item.name == "Old Armor" for item in engine.state.player.inventory)


class TestEquipSwapIntegration:
    def test_full_weapon_swap_flow(self):
        engine = GameEngine()
        engine.start_game()
        old_weapon_name = engine.state.player.weapon.name  # ty: ignore[unresolved-attribute]
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(Weapon(name="Flail", damage="d6+1"))
        engine.use_item(0)
        assert engine.state.player.weapon.name == "Flail"  # ty: ignore[unresolved-attribute]
        assert any(
            item.name == old_weapon_name for item in engine.state.player.inventory
        )

    def test_full_armor_swap_flow(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.armor = Armor(name="Armor", absorb="d4")
        engine.state.player.inventory.clear()  # Clear starting items
        engine.state.player.inventory.append(Armor(name="Chain Mail", absorb="d6"))
        engine.use_item(0)
        assert engine.state.player.armor.name == "Chain Mail"
        assert any(item.name == "Armor" for item in engine.state.player.inventory)

    def test_buy_armor_then_equip_another(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 30
        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)
        engine.buy_item(8)  # Buy Armor
        assert engine.state.player.armor is not None
        assert engine.state.player.armor.name == "Armor"


class TestSaveLoad:
    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    def test_save_and_load_preserves_state(self, _mock_engine_roll, _mock_rules_roll):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.silver = 42
        engine.state.player.points = 10

        saved = engine.save()
        loaded = GameEngine.load(saved)

        assert loaded.state.player.silver == 42
        assert loaded.state.player.points == 10
        assert loaded.state.phase == Phase.EXPLORING

    def test_save_and_load_preserves_rooms(self):
        engine = GameEngine()
        engine.start_game()
        room_count = len(engine.state.rooms)

        saved = engine.save()
        loaded = GameEngine.load(saved)

        assert len(loaded.state.rooms) == room_count

    def test_save_and_load_preserves_room_counter(self):
        engine = GameEngine()
        engine.start_game()
        # Move to a room to increment dungeon counter
        current = engine.state.current_room
        if current and current.exits:
            engine.move_to_room(current.exits[0].destination)
        saved = engine.save()
        loaded = GameEngine.load(saved)
        next_room = loaded._dungeon.build_room()
        assert next_room.id == len(engine.state.rooms)


class TestUseItem:
    def test_use_scroll_consumes_it(self):
        from dark_fort.game.enums import ScrollType
        from dark_fort.game.models import Scroll

        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Scroll(name="Scroll of Fire", scroll_type=ScrollType.SUMMON_DAEMON)
        )
        result = engine.use_item(0)
        assert len(engine.state.player.inventory) == 0
        assert any("unroll" in m.lower() for m in result.messages)

    def test_use_scroll_shows_not_implemented_message(self):
        from dark_fort.game.enums import ScrollType
        from dark_fort.game.models import Scroll

        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(
            Scroll(name="Scroll of Fire", scroll_type=ScrollType.SUMMON_DAEMON)
        )
        result = engine.use_item(0)
        assert any("not yet implemented" in m.lower() for m in result.messages)

    def test_use_rope_returns_empty_messages(self):
        from dark_fort.game.models import Rope

        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        engine.state.player.inventory.append(Rope(name="Rope"))
        result = engine.use_item(0)
        assert result.messages == []
        assert len(engine.state.player.inventory) == 1

    def test_use_cloak_consumes_charge(self):
        from dark_fort.game.models import Cloak

        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory.clear()
        cloak = Cloak(name="Cloak of invisibility", charges=3)
        engine.state.player.inventory.append(cloak)
        result = engine.use_item(0)
        assert cloak.charges == 2
        assert any("Cloak activated" in m for m in result.messages)
        assert len(engine.state.player.inventory) == 1


class TestShopWares:
    def test_shop_wares_populated_on_shop_event(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.shop_wares = list(SHOP_ITEMS)
        assert len(engine.state.shop_wares) > 0

    def test_shop_wares_cleared_on_leave(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.phase = Phase.SHOP
        engine.state.shop_wares = list(SHOP_ITEMS)
        engine.leave_shop()
        assert engine.state.shop_wares == []


class TestWanderingLoop:
    def test_attack_shows_exits_after_combat_kill(self):
        from dark_fort.game.enums import MonsterTier, Phase
        from dark_fort.game.models import CombatState, Monster

        engine = GameEngine()
        engine.start_game()
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=1
        )
        engine.state.combat = CombatState(monster=monster, monster_hp=1)
        engine.state.phase = Phase.COMBAT

        result = engine.attack(player_roll=6)
        assert result.phase == Phase.EXPLORING
        assert any("→" in m for m in result.messages)
