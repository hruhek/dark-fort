from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Command, Phase
from dark_fort.game.models import ActionResult
from dark_fort.game.phase_states import PHASE_STATES
from dark_fort.tui.display import format_inventory, format_shop_wares
from dark_fort.tui.widgets import CommandBar, LogView, StatusBar

if TYPE_CHECKING:
    from dark_fort.tui.app import DarkFortApp


class TitleScreen(Screen):
    """Title screen with centered text and ENTER to start."""

    BINDINGS = [
        ("enter", "start", "Start Game"),
        ("ctrl+q", "quit", "Quit"),
    ]

    @property
    def game_app(self) -> "DarkFortApp":
        return self.app  # ty: ignore[invalid-return-type]

    def compose(self) -> ComposeResult:
        yield Static("DARK FORT", classes="title-header")
        yield Static("A delve into the catacombs", classes="title-subtitle")
        yield Static("Press ENTER to begin", classes="title-footer")
        yield Static("Press CTRL+Q to quit", classes="title-footer")

    def action_start(self) -> None:
        result = self.game_app.engine.start_game()
        self.dismiss()
        self.game_app.push_screen(
            GameScreen(engine=self.game_app.engine, initial_messages=result.messages)
        )


class GameScreen(Screen):
    """Main gameplay screen with log, status bar, and command bar."""

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    selecting_item: reactive[bool] = reactive(False)
    KEY_MAP: dict[str, Command] = {
        "e": Command.EXPLORE,
        "i": Command.INVENTORY,
        "a": Command.ATTACK,
        "f": Command.FLEE,
        "b": Command.BROWSE,
        "l": Command.LEAVE,
    }

    def __init__(
        self, engine: GameEngine, initial_messages: list[str] | None = None
    ) -> None:
        super().__init__()
        self.engine = engine
        self.initial_messages = initial_messages or []

    def compose(self) -> ComposeResult:
        yield StatusBar(
            player=self.engine.state.player,
            explored=self.engine.explored_count,
        )
        yield LogView(id="log")
        yield CommandBar(id="commands")

    def on_mount(self) -> None:
        self.app.sub_title = "Dark Fort"
        log = self.query_one("#log", LogView)
        for msg in self.initial_messages:
            log.add_message(msg)
        self._update_commands()

    def _update_commands(self) -> None:
        phase = self.engine.state.phase
        phase_state = PHASE_STATES.get(phase)
        commands = phase_state.available_commands if phase_state else []

        cmd_bar = self.query_one("#commands", CommandBar)
        cmd_bar.commands = commands

        status_bar = self.query_one(StatusBar)
        status_bar.player = self.engine.state.player
        status_bar.explored = self.engine.explored_count

    def _log_messages(self, messages: list[str]) -> None:
        log = self.query_one("#log", LogView)
        for msg in messages:
            log.add_message(msg)

    def _refresh_status(self) -> None:
        """Force StatusBar refresh by reassigning reactive properties."""
        status_bar = self.query_one(StatusBar)
        status_bar.player = self.engine.state.player
        status_bar.explored = self.engine.explored_count

    def on_key(self, event) -> None:
        # Handle item selection mode (digit keys or Escape)
        if self.selecting_item:
            if event.key == "escape":
                self.selecting_item = False
                self._log_messages(["Cancelled."])
                self._update_commands()
                return
            if event.character and event.character.isdigit():
                digit = int(event.character)
                index = digit - 1 if digit != 0 else 9
                inventory = self.engine.state.player.inventory
                if 0 <= index < len(inventory):
                    result = self.engine.use_item(index)
                    self._log_messages(result.messages)
                    self.selecting_item = False
                    if result.phase:
                        self._handle_phase_change(result)
                    self._update_commands()
                    self._refresh_status()
                else:
                    self._log_messages(["Invalid item number."])
            return

        # Handle command shortcuts
        if event.character and event.character.lower() in self.KEY_MAP:
            key = event.character.lower()
            command = self.KEY_MAP[key]
            phase = self.engine.state.phase
            phase_state = PHASE_STATES.get(phase)
            if phase_state and command in phase_state.available_commands:
                if command == Command.INVENTORY:
                    inventory = self.engine.state.player.inventory
                    if not inventory:
                        self._log_messages(["No items in inventory."])
                        return
                    self.selecting_item = True
                    self._log_messages(format_inventory(self.engine.state))
                    self._log_messages(
                        ["Use item: (type item number or Esc to cancel)"]
                    )
                else:
                    result = self._handle_command(command.value)
                    if result:
                        self._log_messages(result.messages)
                        if result.phase:
                            self._handle_phase_change(result)
                        self._update_commands()
                        self._refresh_status()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("cmd-"):
            return

        action = button_id.replace("cmd-", "")
        command = Command(action)
        if command == Command.INVENTORY:
            inventory = self.engine.state.player.inventory
            if not inventory:
                self._log_messages(["No items in inventory."])
                return
            self.selecting_item = True
            self._log_messages(format_inventory(self.engine.state))
            self._log_messages(["Use item: (type item number or Esc to cancel)"])
            return

        result = self._handle_command(action)
        if result:
            self._log_messages(result.messages)
            if result.phase:
                self._handle_phase_change(result)
            self._update_commands()
            self._refresh_status()

    def _handle_command(self, action: str) -> ActionResult | None:
        phase = self.engine.state.phase
        phase_state = PHASE_STATES.get(phase)
        if phase_state:
            return phase_state.handle_command(self.engine, Command(action))
        return None

    def _handle_phase_change(self, result: ActionResult) -> None:
        self.selecting_item = False
        if result.phase == Phase.GAME_OVER:
            self.dismiss()
            self.app.push_screen(GameOverScreen(engine=self.engine))
        elif result.phase == Phase.VICTORY:
            self.dismiss()
            self.app.push_screen(GameOverScreen(engine=self.engine, victory=True))
        elif result.phase == Phase.SHOP:
            self.dismiss()
            self.app.push_screen(ShopScreen(engine=self.engine))


class ShopScreen(Screen):
    """Void Peddler shop screen."""

    BINDINGS = [
        ("l", "leave", "Leave Shop"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, engine: GameEngine) -> None:
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield StatusBar(
            player=self.engine.state.player,
            explored=self.engine.explored_count,
        )
        yield Static("The Void Peddler", classes="title-header")
        log = LogView(id="shop-log")
        log.can_focus = False
        yield log
        yield CommandBar(id="commands", commands=[Command.LEAVE])

    def on_mount(self) -> None:
        log = self.query_one("#shop-log", LogView)
        for line in format_shop_wares(self.engine.state):
            log.add_message(line)
        self.focus()

    def _refresh_status(self) -> None:
        """Update StatusBar with current state."""
        status_bar = self.query_one(StatusBar)
        status_bar.player = self.engine.state.player
        status_bar.explored = self.engine.explored_count

    def action_leave(self) -> None:
        result = self.engine.leave_shop()
        self.dismiss()
        self.app.push_screen(
            GameScreen(engine=self.engine, initial_messages=result.messages)
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "cmd-leave":
            self.action_leave()

    def on_key(self, event) -> None:
        if event.character and event.character.isdigit():
            digit = int(event.character)
            index = digit - 1 if digit != 0 else 9
            if index < 0 or index >= len(self.engine.state.shop_wares):
                return
            result = self.engine.buy_item(index)
            log = self.query_one("#shop-log", LogView)
            for msg in result.messages:
                log.add_message(msg)
            log.add_message(f"\nYour silver: {self.engine.state.player.silver}s")
            self._refresh_status()


class GameOverScreen(Screen):
    """Game over / victory screen."""

    BINDINGS = [
        ("enter", "restart", "Try Again"),
        ("ctrl+q", "quit", "Quit"),
    ]

    @property
    def game_app(self) -> "DarkFortApp":
        return self.app  # ty: ignore[invalid-return-type]

    def __init__(self, engine: GameEngine, victory: bool = False) -> None:
        super().__init__()
        self.engine = engine
        self.victory = victory

    def compose(self) -> ComposeResult:
        if self.victory:
            yield Static("VICTORY", classes="game-over-header")
        else:
            yield Static("YOU HAVE FALLEN", classes="game-over-header")

        player = self.engine.state.player
        explored = self.engine.explored_count

        yield Static(f"Rooms explored: {explored}", classes="game-over-stats")
        yield Static(f"Points gathered: {player.points}/15", classes="game-over-stats")
        yield Static(f"Silver: {player.silver}", classes="game-over-stats")
        yield Static("Press ENTER to try again", classes="game-over-footer")
        yield Static("Press CTRL+Q to quit", classes="game-over-footer")

    def action_restart(self) -> None:
        self.game_app.engine = GameEngine()
        self.dismiss()
        self.game_app.push_screen(TitleScreen())
