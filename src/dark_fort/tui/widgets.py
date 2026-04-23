from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Label, RichLog

from dark_fort.game.enums import Command
from dark_fort.game.models import Player


class StatusBar(Horizontal):
    """Displays player stats: HP, Silver, Points, Rooms, Weapon, Armor."""

    player: reactive[Player | None] = reactive(None)
    explored: reactive[int] = reactive(0)

    def __init__(self, player: Player | None = None, explored: int = 0) -> None:
        super().__init__()
        self.player = player
        self.explored = explored

    def compose(self) -> ComposeResult:
        yield Label(id="hp")
        yield Label(id="silver")
        yield Label(id="points")
        yield Label(id="rooms")
        yield Label(id="weapon")
        yield Label(id="armor")

    def _refresh(self) -> None:
        if not self.player or not self.is_mounted:
            return

        hp_label = self.query_one("#hp", Label)
        hp_label.update(f"HP: {self.player.hp}/{self.player.max_hp}")

        silver_label = self.query_one("#silver", Label)
        silver_label.update(f"Silver: {self.player.silver}")

        points_label = self.query_one("#points", Label)
        points_label.update(f"Points: {self.player.points}")

        rooms_label = self.query_one("#rooms", Label)
        rooms_label.update(f"Rooms: {self.explored}/12")

        weapon_label = self.query_one("#weapon", Label)
        if self.player.weapon:
            weapon_label.update(
                f"Weapon: {self.player.weapon.name} ({self.player.weapon.damage})"
            )
        else:
            weapon_label.update("Weapon: Unarmed")

        armor_label = self.query_one("#armor", Label)
        if self.player.armor:
            armor_label.update(
                f"Armor: {self.player.armor.name} ({self.player.armor.absorb})"
            )
        else:
            armor_label.update("Armor: None")

    def watch_player(self) -> None:
        self._refresh()

    def watch_explored(self) -> None:
        self._refresh()

    def on_mount(self) -> None:
        self.call_after_refresh(self._refresh)


class LogView(RichLog):
    """Scrollable event log for game messages."""

    message_count: int = 0

    def __init__(self, **kwargs) -> None:
        super().__init__(markup=True, highlight=True, **kwargs)
        self.message_count = 0

    def add_message(self, message: str) -> None:
        self.write(message)
        self.message_count += 1


class CommandBar(Horizontal):
    """Context-sensitive command buttons at the bottom of the screen."""

    commands: reactive[list[Command]] = reactive([])

    def __init__(self, commands: list[Command] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.commands = commands or []

    @staticmethod
    def _format_button_label(cmd: Command) -> str:
        """Format button label with shortcut hint: [A]ttack"""
        name = cmd.value.replace("_", " ").title()
        if name:
            return f"[[{name[0]}]]{name[1:]}"
        return name

    def compose(self) -> ComposeResult:
        for cmd in self.commands:
            button = Button(self._format_button_label(cmd), id=f"cmd-{cmd.value}")
            yield button

    def watch_commands(self) -> None:
        if not self.is_mounted:
            return
        self.remove_children()
        for cmd in self.commands:
            button = Button(self._format_button_label(cmd), id=f"cmd-{cmd.value}")
            self.mount(button)
