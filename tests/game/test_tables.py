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
    get_tough_monster,
    get_weak_monster,
)


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

    def test_get_weak_monster_by_index(self):
        monster = get_weak_monster(0)
        assert monster.name == "Blood-Drenched Skeleton"


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

    def test_get_tough_monster_by_index(self):
        monster = get_tough_monster(0)
        assert monster.name == "Necro-Sorcerer"


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
