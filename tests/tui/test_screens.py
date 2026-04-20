from dark_fort.game.enums import Command, ItemType, MonsterTier, Phase
from dark_fort.game.models import CombatState, Item, Monster
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import ShopScreen
from dark_fort.tui.widgets import CommandBar


class TestTitleScreen:
    async def test_pressing_enter_starts_game(self):
        async with DarkFortApp().run_test() as pilot:
            assert pilot.app.screen.__class__.__name__ == "TitleScreen"
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    async def test_starting_game_sets_exploring_phase(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]


class TestGameScreenPhaseCommands:
    async def test_exploring_phase_shows_explore_and_inventory(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.EXPLORE in cmd_bar.commands
            assert Command.INVENTORY in cmd_bar.commands

    async def test_combat_phase_shows_attack_flee_use_item(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.ATTACK in cmd_bar.commands
            assert Command.FLEE in cmd_bar.commands
            assert Command.USE_ITEM in cmd_bar.commands

    async def test_shop_phase_shows_browse_and_leave(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.BROWSE in cmd_bar.commands
            assert Command.LEAVE in cmd_bar.commands


class TestGameScreenActions:
    async def test_attack_button_triggers_combat(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            attack_button = pilot.app.screen.query_one("#cmd-attack")
            await pilot.click(attack_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    async def test_flee_button_returns_to_exploring(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
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

    async def test_explore_button_enters_new_room(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_rooms = dict(pilot.app.engine.state.rooms)  # ty: ignore[unresolved-attribute]
            explore_button = pilot.app.screen.query_one("#cmd-explore")
            await pilot.click(explore_button)
            await pilot.pause()
            # Room event may trigger shop (pushes ShopScreen) or combat (stays on GameScreen)
            if pilot.app.screen.__class__.__name__ == "ShopScreen":
                await pilot.press("l")
                await pilot.pause()
            # Verify a new room was added
            assert len(pilot.app.engine.state.rooms) > len(initial_rooms)  # ty: ignore[unresolved-attribute]

    async def test_inventory_button_shows_empty_message(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            inv_button = pilot.app.screen.query_one("#cmd-inventory")
            await pilot.click(inv_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    async def test_inventory_button_shows_items(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Item(name="Potion", type=ItemType.POTION, damage="d6")
            )
            inv_button = pilot.app.screen.query_one("#cmd-inventory")
            await pilot.click(inv_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    async def test_leave_button_returns_to_exploring(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]


class TestShopScreen:
    async def test_shop_displays_items_on_mount(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "ShopScreen"
            shop_log = pilot.app.screen.query_one("#shop-log")
            assert shop_log.message_count > 0  # ty: ignore[unresolved-attribute]

    async def test_buy_item_deducts_silver(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 20  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == 16  # ty: ignore[unresolved-attribute]

    async def test_leave_shop_returns_to_game_screen(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]


class TestGameOverScreen:
    async def test_death_screen_shows_fallen_message(self):
        from dark_fort.tui.screens import GameOverScreen

        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is False  # ty: ignore[unresolved-attribute]

    async def test_victory_screen_shows_victory_message(self):
        from dark_fort.tui.screens import GameOverScreen

        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.level_benefits = [1, 2, 3, 4, 5, 6]  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine, victory=True))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameOverScreen"
            assert pilot.app.screen.victory is True  # ty: ignore[unresolved-attribute]

    async def test_restart_resets_engine(self):
        from dark_fort.tui.screens import GameOverScreen

        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 0  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "TitleScreen"
            assert pilot.app.engine.state.phase == Phase.TITLE  # ty: ignore[unresolved-attribute]
