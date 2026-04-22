from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Command, Phase, ScrollType
from dark_fort.game.models import Potion, Scroll
from dark_fort.game.phase_states import (
    PHASE_STATES,
    CombatPhaseState,
    ExploringPhaseState,
    ShopPhaseState,
)
from dark_fort.game.tables import SHOP_ITEMS


class TestPhaseStateRegistry:
    def test_registry_has_all_phases(self):
        assert Phase.EXPLORING in PHASE_STATES
        assert Phase.COMBAT in PHASE_STATES
        assert Phase.SHOP in PHASE_STATES

    def test_registry_values_are_instances(self):
        assert isinstance(PHASE_STATES[Phase.EXPLORING], ExploringPhaseState)
        assert isinstance(PHASE_STATES[Phase.COMBAT], CombatPhaseState)
        assert isinstance(PHASE_STATES[Phase.SHOP], ShopPhaseState)


class TestExploringPhaseState:
    def test_phase_is_exploring(self):
        state = ExploringPhaseState()
        assert state.phase == Phase.EXPLORING

    def test_available_commands(self):
        state = ExploringPhaseState()
        assert state.available_commands == [Command.EXPLORE, Command.INVENTORY]

    def test_handle_explore_delegates_to_engine(self):
        engine = GameEngine()
        engine.start_game()
        state = ExploringPhaseState()
        result = state.handle_command(engine, Command.EXPLORE)
        assert result is not None
        assert result.messages

    def test_handle_inventory_empty(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory = []
        state = ExploringPhaseState()
        result = state.handle_command(engine, Command.INVENTORY)
        assert result is not None
        assert result.messages == []

    def test_handle_inventory_with_items(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.player.inventory = [
            Potion(name="Potion", heal="d6"),
            Scroll(name="Scroll", scroll_type=ScrollType.SUMMON_DAEMON),
        ]
        state = ExploringPhaseState()
        result = state.handle_command(engine, Command.INVENTORY)
        assert result is not None
        assert result.messages == []

    def test_handle_unknown_returns_none(self):
        engine = GameEngine()
        engine.start_game()
        state = ExploringPhaseState()
        assert state.handle_command(engine, Command.MOVE) is None


class TestCombatPhaseState:
    def test_phase_is_combat(self):
        state = CombatPhaseState()
        assert state.phase == Phase.COMBAT

    def test_available_commands(self):
        state = CombatPhaseState()
        assert state.available_commands == [
            Command.ATTACK,
            Command.FLEE,
            Command.USE_ITEM,
        ]

    def test_handle_attack_without_combat(self):
        engine = GameEngine()
        engine.start_game()
        state = CombatPhaseState()
        result = state.handle_command(engine, Command.ATTACK)
        assert result is not None
        assert "No monster to attack" in result.messages[0]

    def test_handle_flee_without_combat(self):
        engine = GameEngine()
        engine.start_game()
        state = CombatPhaseState()
        result = state.handle_command(engine, Command.FLEE)
        assert result is not None
        assert "No monster to flee" in result.messages[0]

    def test_handle_use_item(self):
        engine = GameEngine()
        engine.start_game()
        state = CombatPhaseState()
        result = state.handle_command(engine, Command.USE_ITEM)
        assert result is not None
        assert "Use item" in result.messages[0]

    def test_handle_unknown_returns_none(self):
        engine = GameEngine()
        engine.start_game()
        state = CombatPhaseState()
        assert state.handle_command(engine, Command.MOVE) is None


class TestShopPhaseState:
    def test_phase_is_shop(self):
        state = ShopPhaseState()
        assert state.phase == Phase.SHOP

    def test_available_commands(self):
        state = ShopPhaseState()
        assert state.available_commands == [Command.BROWSE, Command.LEAVE]

    def test_handle_leave_returns_to_exploring(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.phase = Phase.SHOP
        state = ShopPhaseState()
        result = state.handle_command(engine, Command.LEAVE)
        assert result is not None
        assert result.phase == Phase.EXPLORING

    def test_handle_browse_shows_items(self):
        engine = GameEngine()
        engine.start_game()
        engine.state.shop_wares = list(SHOP_ITEMS)
        state = ShopPhaseState()
        result = state.handle_command(engine, Command.BROWSE)
        assert result is not None
        assert result.messages == []

    def test_handle_unknown_returns_none(self):
        engine = GameEngine()
        engine.start_game()
        state = ShopPhaseState()
        assert state.handle_command(engine, Command.MOVE) is None
