from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from dark_fort.game.engine import GameEngine
from dark_fort.game.enums import Command, Phase
from dark_fort.game.models import ActionResult
from dark_fort.game.phase_states import PHASE_STATES
from dark_fort.game.tables import SHOP_ITEMS
from dark_fort.tui.widgets import CommandBar, LogView, StatusBar

if TYPE_CHECKING:
    from dark_fort.tui.app import DarkFortApp


class TitleScreen(Screen):
    """Title screen with centered text and ENTER to start."""

    BINDINGS = [("enter", "start", "Start Game")]

    @property
    def game_app(self) -> "DarkFortApp":
        return self.app  # ty: ignore[invalid-return-type]

    def compose(self) -> ComposeResult:
        yield Static("DARK FORT", classes="title-header")
        yield Static("A delve into the catacombs", classes="title-subtitle")
        yield Static("Press ENTER to begin", classes="title-footer")

    def action_start(self) -> None:
        result = self.game_app.engine.start_game()
        self.dismiss()
        self.game_app.push_screen(
            GameScreen(engine=self.game_app.engine, initial_messages=result.messages)
        )


class GameScreen(Screen):
    """Main gameplay screen with log, status bar, and command bar."""

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
        state = PHASE_STATES.get(phase)
        commands = state.available_commands if state else []

        cmd_bar = self.query_one("#commands", CommandBar)
        cmd_bar.commands = commands

        status_bar = self.query_one(StatusBar)
        status_bar.player = self.engine.state.player
        status_bar.explored = self.engine.explored_count

    def _log_messages(self, messages: list[str]) -> None:
        log = self.query_one("#log", LogView)
        for msg in messages:
            log.add_message(msg)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if not button_id.startswith("cmd-"):
            return

        action = button_id.replace("cmd-", "")
        result = self._handle_command(action)
        if result:
            self._log_messages(result.messages)
            if result.phase:
                self._handle_phase_change(result)
            self._update_commands()

    def _handle_command(self, action: str) -> ActionResult | None:
        phase = self.engine.state.phase
        state = PHASE_STATES.get(phase)
        if state:
            return state.handle_command(self.engine, Command(action))
        return None

    def _handle_phase_change(self, result: ActionResult) -> None:
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

    BINDINGS = [("l", "leave", "Leave Shop")]

    def __init__(self, engine: GameEngine) -> None:
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static("The Void Peddler", classes="title-header")
        log = LogView(id="shop-log")
        log.can_focus = False
        yield log
        yield CommandBar(id="commands", commands=[Command.LEAVE])

    def on_mount(self) -> None:
        log = self.query_one("#shop-log", LogView)
        log.add_message("Available wares:")
        for i, entry in enumerate(SHOP_ITEMS):
            log.add_message(f"  {i + 1}. {entry.display_stats()}")
        log.add_message(f"\nYour silver: {self.engine.state.player.silver}s")
        log.add_message("Press 1-9, 0 for item 10, or L to leave.")
        self.focus()

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
            if index < 0 or index >= len(SHOP_ITEMS):
                return
            result = self.engine.buy_item(index)
            log = self.query_one("#shop-log", LogView)
            for msg in result.messages:
                log.add_message(msg)
            log.add_message(f"\nYour silver: {self.engine.state.player.silver}s")


class GameOverScreen(Screen):
    """Game over / victory screen."""

    BINDINGS = [("enter", "restart", "Try Again")]

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

    def action_restart(self) -> None:
        self.game_app.engine = GameEngine()
        self.dismiss()
        self.game_app.push_screen(TitleScreen())
