from dark_fort.game.enums import MonsterTier, Phase
from dark_fort.game.models import CombatState, Monster
from dark_fort.game.tables import SHOP_ITEMS
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import GameOverScreen, ShopScreen


class TestDeathFlow:
    async def test_player_dies_from_combat_damage(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 1  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.armor = None  # ty: ignore[unresolved-attribute]
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=10, damage="d4", hp=100
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=100)  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            attack_button = pilot.app.screen.query_one("#cmd-attack")
            await pilot.click(attack_button)
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is False  # ty: ignore[unresolved-attribute]

    async def test_player_dies_when_hp_reaches_zero(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0  # ty: ignore[unresolved-attribute]
            result = pilot.app.engine.check_game_over()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert result.phase == Phase.GAME_OVER
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"


class TestFleeFlow:
    async def test_flee_returns_to_exploring_with_damage(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_hp = pilot.app.engine.state.player.hp  # ty: ignore[unresolved-attribute]
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            flee_button = pilot.app.screen.query_one("#cmd-flee")
            await pilot.click(flee_button)
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            assert pilot.app.engine.state.combat is None  # ty: ignore[unresolved-attribute]
            assert pilot.app.engine.state.player.hp < initial_hp


class TestShopFlow:
    async def test_buy_item_and_leave_shop(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 20  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == 16  # ty: ignore[unresolved-attribute]
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            assert pilot.app.engine.state.phase == Phase.EXPLORING

    async def test_cannot_buy_without_enough_silver(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 2  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            initial_silver = pilot.app.engine.state.player.silver  # ty: ignore[unresolved-attribute]
            await pilot.press("8")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == initial_silver  # ty: ignore[unresolved-attribute]


class TestVictoryFlow:
    async def test_all_benefits_claimed_triggers_victory(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]  # ty: ignore[unresolved-attribute]
            result = pilot.app.engine.check_victory()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert result.phase == Phase.VICTORY
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine, victory=True))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is True  # ty: ignore[unresolved-attribute]

    async def test_victory_screen_shows_explored_count(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]  # ty: ignore[unresolved-attribute]
            pilot.app.engine.check_victory()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine, victory=True))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            stats_widgets = list(pilot.app.screen.query(".game-over-stats"))
            assert len(stats_widgets) == 3


class TestWanderingFlow:
    async def test_wandering_move_to_exit(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.combat = None  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            # Press M to activate exit selection
            await pilot.press("m")
            await pilot.pause()
            # Pick first exit number (door 1)
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.phase != Phase.GAME_OVER  # ty: ignore[unresolved-attribute]

    async def test_escape_cancels_exit_selection(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.combat = None  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("m")
            await pilot.pause()
            assert pilot.app.screen.selecting_exit is True  # ty: ignore[unresolved-attribute]
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.screen.selecting_exit is False  # ty: ignore[unresolved-attribute]

    async def test_digit_without_move_mode_does_nothing(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.combat = None  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            initial_room = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            assert pilot.app.screen.selecting_exit is False  # ty: ignore[unresolved-attribute]
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.current_room.id == initial_room  # ty: ignore[unresolved-attribute]

    async def test_invalid_exit_number_shows_error(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.combat = None  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("m")
            await pilot.pause()
            await pilot.press("9")
            await pilot.pause()
            assert pilot.app.screen.selecting_exit is True  # ty: ignore[unresolved-attribute]
