from dark_fort.game.enums import MonsterTier, Phase
from dark_fort.game.models import CombatState, Monster
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import GameOverScreen


class TestDeathFlow:
    async def test_player_dies_from_combat_damage(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 1  # ty: ignore[unresolved-attribute]
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
            cmd_bar = pilot.app.screen.query_one("#cmd-explore")
            assert cmd_bar is not None
