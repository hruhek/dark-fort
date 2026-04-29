from unittest.mock import patch

import pytest

from dark_fort.game.enums import MonsterTier
from dark_fort.game.tables import (
    ARMOR_TABLE,
    ENTRANCE_RESULTS,
    ITEMS_TABLE,
    LEVEL_BENEFITS,
    ROOM_RESULTS,
    ROOM_SHAPES,
    SCROLLS_TABLE,
    SHOP_ITEMS,
    TOUGH_MONSTERS,
    WEAK_MONSTERS,
    WEAPONS_TABLE,
    get_room_shape,
    get_shop_item,
    roll_on_table,
)


class TestRollOnTable:
    @patch("dark_fort.game.tables.roll", return_value=1)
    def test_returns_first_element_when_roll_is_1(self, _mock_roll):
        result = roll_on_table(WEAK_MONSTERS, "d4")
        assert result.name == "Blood-Drenched Skeleton"

    @patch("dark_fort.game.tables.roll", return_value=4)
    def test_returns_last_element_when_roll_equals_length(self, _mock_roll):
        result = roll_on_table(WEAK_MONSTERS, "d4")
        assert result.name == "Undead Hound"

    @patch("dark_fort.game.tables.roll", return_value=2)
    def test_returns_second_element(self, _mock_roll):
        result = roll_on_table(WEAPONS_TABLE, "d4")
        assert result.name == "Dagger"

    def test_raises_index_error_when_out_of_bounds(self):
        with (
            patch("dark_fort.game.tables.roll", return_value=99),
            pytest.raises(IndexError),
        ):
            roll_on_table(WEAK_MONSTERS, "d4")

    @patch("dark_fort.game.tables.roll", return_value=3)
    def test_works_with_string_tables(self, _mock_roll):
        table = ["a", "b", "c", "d"]
        result = roll_on_table(table, "d4")
        assert result == "c"

    @patch("dark_fort.game.tables.roll", return_value=1)
    def test_works_with_enum_tables(self, _mock_roll):
        result = roll_on_table(ROOM_RESULTS, "d6")
        assert result == ROOM_RESULTS[0]


class TestWeakMonsters:
    def test_four_weak_monsters(self):
        assert len(WEAK_MONSTERS) == 4

    def test_all_have_required_fields(self):
        for m in WEAK_MONSTERS:
            assert m.name
            assert m.tier == MonsterTier.WEAK
            assert m.points > 0
            assert m.damage
            assert m.hp > 0


class TestToughMonsters:
    def test_four_tough_monsters(self):
        assert len(TOUGH_MONSTERS) == 4

    def test_all_have_required_fields(self):
        for m in TOUGH_MONSTERS:
            assert m.name
            assert m.tier == MonsterTier.TOUGH
            assert m.points > 0
            assert m.damage
            assert m.hp > 0


class TestShopItems:
    def test_shop_has_items(self):
        assert len(SHOP_ITEMS) > 0

    def test_all_have_price(self):
        for entry in SHOP_ITEMS:
            assert entry.price > 0

    def test_get_shop_item_by_index(self):
        entry = get_shop_item(0)
        assert entry.price == 4


class TestRoomShapes:
    def test_shapes_for_2d6(self):
        assert len(ROOM_SHAPES) == 11

    def test_get_room_shape(self):
        assert get_room_shape(2) == "Irregular cave"
        assert get_room_shape(7) == "Square"


class TestRoomResults:
    def test_six_room_results(self):
        assert len(ROOM_RESULTS) == 6


class TestEntranceResults:
    def test_four_entrance_results(self):
        assert len(ENTRANCE_RESULTS) == 4

    def test_all_are_room_events(self):
        from dark_fort.game.enums import RoomEvent

        for entry in ENTRANCE_RESULTS:
            assert isinstance(entry, RoomEvent)


class TestItemsTable:
    def test_six_items(self):
        assert len(ITEMS_TABLE) == 6


class TestScrollsTable:
    def test_four_scrolls(self):
        assert len(SCROLLS_TABLE) == 4


class TestWeaponsTable:
    def test_four_weapons(self):
        assert len(WEAPONS_TABLE) == 4


class TestLevelBenefits:
    def test_six_benefits(self):
        assert len(LEVEL_BENEFITS) == 6


class TestArmorTable:
    def test_armor_table_has_entries(self):
        assert len(ARMOR_TABLE) >= 1

    def test_armor_table_first_entry(self):
        armor = ARMOR_TABLE[0]
        assert armor.name == "Armor"
        assert armor.absorb == "d4"


class TestShopItemsArmor:
    def test_armor_shop_item_has_absorb(self):
        from dark_fort.game.models import Armor

        armor_items = [entry for entry in SHOP_ITEMS if isinstance(entry.item, Armor)]
        assert len(armor_items) >= 1
        armor = armor_items[0].item
        assert isinstance(armor, Armor)
        assert armor.absorb == "d4"
        assert armor_items[0].price == 10
