from dark_fort.game.enums import Phase, ScrollType
from dark_fort.game.models import Armor, GameState, Potion, Scroll, Weapon
from dark_fort.game.tables import SHOP_ITEMS
from dark_fort.tui.display import format_inventory, format_shop_wares


class TestFormatInventory:
    def test_empty_inventory(self):
        state = GameState(phase=Phase.EXPLORING)
        result = format_inventory(state)
        assert result == ["Your inventory is empty."]

    def test_inventory_with_potion(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Potion(name="Potion", heal="d6")]
        result = format_inventory(state)
        assert result[0] == "Inventory:"
        assert "Potion" in result[1]
        assert "[P]" in result[1]

    def test_inventory_with_weapon(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Weapon(name="Sword", damage="d6", attack_bonus=1)]
        result = format_inventory(state)
        assert "[W]" in result[1]
        assert "d6/+1" in result[1]

    def test_inventory_with_armor(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [Armor(name="Armor", absorb="d4")]
        result = format_inventory(state)
        assert "[A]" in result[1]
        assert "d4" in result[1]

    def test_inventory_with_scroll(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [
            Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON)
        ]
        result = format_inventory(state)
        assert "[S]" in result[1]

    def test_inventory_with_multiple_items(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.inventory = [
            Potion(name="Potion", heal="d6"),
            Weapon(name="Sword", damage="d6"),
        ]
        result = format_inventory(state)
        assert len(result) == 3


class TestFormatShopWares:
    def test_format_shop_wares(self):
        state = GameState(phase=Phase.SHOP)
        state.shop_wares = list(SHOP_ITEMS)
        result = format_shop_wares(state)
        assert result[0] == "Available wares:"
        assert any("Potion" in line for line in result)
        assert any("silver" in line.lower() for line in result)

    def test_empty_shop_wares(self):
        state = GameState(phase=Phase.SHOP)
        result = format_shop_wares(state)
        assert result[0] == "Available wares:"
        assert "Your silver:" in result[-2]
