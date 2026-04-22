from dark_fort.game.enums import ActionKind, EquipSlot


class TestActionKind:
    def test_action_kind_values(self):
        assert ActionKind.INVENTORY == "inventory"
        assert ActionKind.COMBAT == "combat"
        assert ActionKind.SHOP == "shop"
        assert ActionKind.ROOM == "room"
        assert ActionKind.NAVIGATION == "navigation"
        assert ActionKind.LEVEL_UP == "level_up"

    def test_action_kind_is_str(self):
        assert isinstance(ActionKind.INVENTORY, str)


class TestEquipSlot:
    def test_equip_slot_values(self):
        assert EquipSlot.WEAPON == "weapon"
        assert EquipSlot.ARMOR == "armor"
        assert EquipSlot.NONE == "none"
        assert EquipSlot.SPECIAL == "special"

    def test_equip_slot_is_str(self):
        assert isinstance(EquipSlot.WEAPON, str)
