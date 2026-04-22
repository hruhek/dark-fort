from dark_fort.game.enums import MonsterTier, Phase, RoomEvent
from dark_fort.game.models import Player, RoomEventResult, Rope
from dark_fort.game.rules import resolve_room_event


class TestRoomEventResult:
    def test_empty_room(self):
        player = Player()
        result = resolve_room_event(RoomEvent.EMPTY, player)
        assert isinstance(result, RoomEventResult)
        assert result.explored is True
        assert result.phase is None
        assert result.combat is None

    def test_pit_trap_no_rope(self):
        player = Player(hp=15)
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta < 0

    def test_pit_trap_with_rope_safe(self):
        player = Player(hp=15)
        player.inventory.append(Rope(name="Rope"))
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=4)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta == 0
        assert result.explored is True

    def test_pit_trap_death(self):
        player = Player(hp=1)
        result = resolve_room_event(RoomEvent.PIT_TRAP, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.GAME_OVER

    def test_weak_monster(self):
        player = Player()
        result = resolve_room_event(RoomEvent.WEAK_MONSTER, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.COMBAT
        assert result.combat is not None
        assert result.combat.monster.tier == MonsterTier.WEAK

    def test_tough_monster(self):
        player = Player()
        result = resolve_room_event(RoomEvent.TOUGH_MONSTER, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.COMBAT
        assert result.combat is not None
        assert result.combat.monster.tier == MonsterTier.TOUGH

    def test_shop(self):
        player = Player()
        result = resolve_room_event(RoomEvent.SHOP, player)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.SHOP
        assert result.combat is None

    def test_soothsayer_reward(self):
        player = Player(silver=0)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=1)
        assert isinstance(result, RoomEventResult)
        assert result.silver_delta == 10
        assert result.explored is True

    def test_soothsayer_curse(self):
        player = Player(hp=15)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.hp_delta < 0
        assert result.explored is True

    def test_soothsayer_curse_death(self):
        player = Player(hp=1)
        result = resolve_room_event(RoomEvent.SOOTHSAYER, player, dice_roll=2)
        assert isinstance(result, RoomEventResult)
        assert result.phase == Phase.GAME_OVER

    def test_does_not_mutate_player_hp_for_empty(self):
        player = Player(hp=15)
        resolve_room_event(RoomEvent.EMPTY, player)
        assert player.hp == 15

    def test_does_not_mutate_player_silver_for_empty(self):
        player = Player(silver=10)
        resolve_room_event(RoomEvent.EMPTY, player)
        assert player.silver == 10
