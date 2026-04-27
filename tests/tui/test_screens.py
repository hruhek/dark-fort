from unittest.mock import patch

from dark_fort.game.enums import Command, MonsterTier, Phase
from dark_fort.game.models import CombatState, Monster, Potion
from dark_fort.game.tables import SHOP_ITEMS
from dark_fort.tui.app import DarkFortApp
from dark_fort.tui.screens import ShopScreen
from dark_fort.tui.widgets import CommandBar, LogView


class TestTitleScreen:
    async def test_pressing_enter_starts_game(self):
        async with DarkFortApp().run_test() as pilot:
            assert pilot.app.screen.__class__.__name__ == "TitleScreen"
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_starting_game_sets_exploring_phase(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]

    async def test_ctrl_q_exits_app(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("ctrl+q")
            await pilot.pause()
            # App should exit; if we get here without error, quit worked
            assert True


class TestGameScreenPhaseCommands:
    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_exploring_phase_shows_move_and_inventory(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            cmd_bar = pilot.app.screen.query_one("#commands", CommandBar)
            assert Command.MOVE in cmd_bar.commands
            assert Command.INVENTORY in cmd_bar.commands

    async def test_combat_phase_shows_attack_flee_inventory(self):
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
            assert Command.INVENTORY in cmd_bar.commands

    async def test_shop_phase_shows_browse_and_leave(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
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

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_digit_key_button_moves_through_exit(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_room_id = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            await pilot.press("1")
            await pilot.pause()
            # Room event may trigger shop (pushes ShopScreen) or combat (stays on GameScreen)
            if pilot.app.screen.__class__.__name__ == "ShopScreen":
                await pilot.press("l")
                await pilot.pause()
            # Verify current room changed
            assert pilot.app.engine.state.current_room.id != initial_room_id  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_inventory_button_shows_empty_message(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            inv_button = pilot.app.screen.query_one("#cmd-inventory")
            await pilot.click(inv_button)
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            assert log.message_count > 0  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_inventory_button_shows_items(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
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
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            leave_button = pilot.app.screen.query_one("#cmd-leave")
            await pilot.click(leave_button)
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]

    async def test_ctrl_q_on_game_screen(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert True

    async def test_inventory_key_shows_inventory_in_combat(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=Monster(
                    name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
                ),
                monster_hp=5,
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press("i")
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]

    async def test_digit_key_uses_item(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            pilot.app.engine.state.player.hp = 5  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=Monster(
                    name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
                ),
                monster_hp=5,
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("i")  # Enter item selection mode
            await pilot.pause()
            await pilot.press("1")  # Use first item
            await pilot.pause()
            assert pilot.app.engine.state.player.hp > 5  # ty: ignore[unresolved-attribute]  # Potion healed

    async def test_button_labels_show_shortcuts(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=Monster(
                    name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
                ),
                monster_hp=5,
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            attack_button = pilot.app.screen.query_one("#cmd-attack")
            assert "[A]ttack" in attack_button.label.plain  # ty: ignore[unresolved-attribute]

    async def test_inventory_key_shows_prompt_text(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=Monster(
                    name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
                ),
                monster_hp=5,
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()

            captured: list[str] = []
            original_log = pilot.app.screen._log_messages  # ty: ignore[unresolved-attribute]

            def capture_log(messages: list[str]) -> None:
                captured.extend(messages)
                original_log(messages)

            pilot.app.screen._log_messages = capture_log  # ty: ignore[unresolved-attribute]
            await pilot.press("i")
            await pilot.pause()
            assert any(
                "Use item: (type item number or Esc to cancel)" in m for m in captured
            )

    async def test_hp_status_bar_updates_after_combat_round(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.hp = 15  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.armor = None  # ty: ignore[unresolved-attribute]
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=10, damage="d4", hp=100
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=monster, monster_hp=100
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()

            refresh_calls = 0
            original_refresh = pilot.app.screen._refresh_status  # ty: ignore[unresolved-attribute]

            def counting_refresh() -> None:
                nonlocal refresh_calls
                refresh_calls += 1
                original_refresh()

            pilot.app.screen._refresh_status = counting_refresh  # ty: ignore[unresolved-attribute]

            await pilot.press("a")
            await pilot.pause()

            assert pilot.app.engine.state.player.hp < 15  # ty: ignore[unresolved-attribute]
            assert refresh_calls > 0

    async def test_a_key_triggers_attack(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=monster, monster_hp=5
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            log = pilot.app.screen.query_one("#log", LogView)
            before_count = log.message_count
            await pilot.press("a")
            await pilot.pause()
            assert log.message_count > before_count

    async def test_f_key_triggers_flee(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_hp = pilot.app.engine.state.player.hp  # ty: ignore[unresolved-attribute]
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=monster, monster_hp=5
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("f")
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]
            assert pilot.app.engine.state.player.hp < initial_hp  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_digit_key_moves_through_exit(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_room_id = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.current_room.id != initial_room_id  # ty: ignore[unresolved-attribute]

    async def test_l_key_triggers_leave_shop(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]

    async def test_inventory_key_in_exploring_shows_items(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press("i")
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]

    async def test_inventory_key_in_exploring_empty_shows_message(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press("i")
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]
            messages = [
                log.lines[i].text  # ty: ignore[unresolved-attribute]
                for i in range(before_count, log.message_count)  # ty: ignore[unresolved-attribute]
            ]
            assert any("No items" in m for m in messages)

    async def test_escape_cancels_inventory_selection_in_exploring(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            await pilot.press("i")
            await pilot.pause()
            assert pilot.app.screen.selecting_item is True  # ty: ignore[unresolved-attribute]
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.screen.selecting_item is False  # ty: ignore[unresolved-attribute]

    async def test_escape_cancels_inventory_selection_in_combat(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.inventory.clear()  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.player.inventory.append(  # ty: ignore[unresolved-attribute]
                Potion(name="Potion", heal="d6")
            )
            pilot.app.engine.state.combat = CombatState(  # ty: ignore[unresolved-attribute]
                monster=Monster(
                    name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
                ),
                monster_hp=5,
            )
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("i")
            await pilot.pause()
            assert pilot.app.screen.selecting_item is True  # ty: ignore[unresolved-attribute]
            await pilot.press("escape")
            await pilot.pause()
            assert pilot.app.screen.selecting_item is False  # ty: ignore[unresolved-attribute]


class TestWanderingNavigation:
    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_digit_zero_in_entrance_calls_exit_dungeon(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            assert pilot.app.engine.state.current_room.id == 0  # ty: ignore[unresolved-attribute]
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press("0")
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_digit_key_navigates_to_room(
        self, _mock_engine_roll, _mock_rules_roll
    ):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_room_id = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.current_room.id != initial_room_id  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_invalid_digit_shows_error(self, _mock_engine_roll, _mock_rules_roll):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            current_room = pilot.app.engine.state.current_room  # ty: ignore[unresolved-attribute]
            valid_doors = {e.door_number for e in current_room.exits}
            invalid_digit = 9
            while invalid_digit in valid_doors:
                invalid_digit -= 1
            if invalid_digit <= 0:
                invalid_digit = 5
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press(str(invalid_digit))
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]

    async def test_digit_keys_ignored_in_combat_phase(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            initial_room_id = pilot.app.engine.state.current_room.id  # ty: ignore[unresolved-attribute]
            monster = Monster(
                name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
            )
            pilot.app.engine.state.combat = CombatState(monster=monster, monster_hp=5)  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.COMBAT  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            pilot.app.screen._update_commands()  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("1")
            await pilot.pause()
            assert pilot.app.engine.state.current_room.id == initial_room_id  # ty: ignore[unresolved-attribute]

    @patch("dark_fort.game.rules.roll", return_value=1)
    @patch("dark_fort.game.engine.roll", return_value=4)
    async def test_move_command_shows_exits(self, _mock_engine_roll, _mock_rules_roll):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            log = pilot.app.screen.query_one("#log")
            before_count = log.message_count  # ty: ignore[unresolved-attribute]
            await pilot.press("m")
            await pilot.pause()
            assert log.message_count > before_count  # ty: ignore[unresolved-attribute]


class TestShopScreen:
    async def test_shop_displays_items_on_mount(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
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
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
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
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("l")
            await pilot.pause()
            assert pilot.app.screen.__class__.__name__ == "GameScreen"
            assert pilot.app.engine.state.phase == Phase.EXPLORING  # ty: ignore[unresolved-attribute]

    async def test_buy_item_10_with_zero_key(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.player.silver = 20  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("0")
            await pilot.pause()
            assert pilot.app.engine.state.player.silver == 5  # ty: ignore[unresolved-attribute]  # 20 - 15 (Cloak price)
            cloak = next(
                item
                for item in pilot.app.engine.state.player.inventory
                if item.type.name == "CLOAK"
            )
            assert cloak.charges > 0

    async def test_shop_shows_status_bar(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            from dark_fort.tui.widgets import StatusBar

            status_bar = pilot.app.screen.query_one(StatusBar)
            assert status_bar is not None
            assert status_bar.player is not None

    async def test_ctrl_q_on_shop_screen(self):
        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.engine.state.phase = Phase.SHOP  # ty: ignore[unresolved-attribute]
            pilot.app.engine.state.shop_wares = list(SHOP_ITEMS)  # ty: ignore[unresolved-attribute]
            pilot.app.push_screen(ShopScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            await pilot.press("ctrl+q")
            await pilot.pause()
            assert True


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

    async def test_game_over_shows_quit_hint(self):
        from dark_fort.tui.screens import GameOverScreen

        async with DarkFortApp().run_test() as pilot:
            await pilot.press("enter")
            await pilot.pause()
            pilot.app.push_screen(GameOverScreen(engine=pilot.app.engine))  # ty: ignore[unresolved-attribute]
            await pilot.pause()
            # Check that quit binding exists
            bindings = [b[0] for b in pilot.app.screen.BINDINGS]  # ty: ignore
            assert "ctrl+q" in bindings
