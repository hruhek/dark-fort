from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dark_fort.game.enums import Command, Phase
from dark_fort.game.models import ActionResult

if TYPE_CHECKING:
    from dark_fort.game.engine import GameEngine


class PhaseState(ABC):
    @property
    @abstractmethod
    def phase(self) -> Phase: ...

    @property
    @abstractmethod
    def available_commands(self) -> list[Command]: ...

    @abstractmethod
    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None: ...


class ExploringPhaseState(PhaseState):
    phase = Phase.EXPLORING
    available_commands = [Command.MOVE, Command.INVENTORY]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.MOVE:
            return ActionResult(messages=engine.get_room_exits())
        if action == Command.INVENTORY:
            return ActionResult(messages=[])
        return None


class CombatPhaseState(PhaseState):
    phase = Phase.COMBAT
    available_commands = [Command.ATTACK, Command.FLEE, Command.INVENTORY]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.ATTACK:
            return engine.attack()
        if action == Command.FLEE:
            return engine.flee()
        if action == Command.INVENTORY:
            # Return empty result; GameScreen handles inventory display
            return ActionResult(messages=[])
        return None


class ShopPhaseState(PhaseState):
    phase = Phase.SHOP
    available_commands = [Command.BROWSE, Command.LEAVE]

    def handle_command(
        self, engine: GameEngine, action: Command
    ) -> ActionResult | None:
        if action == Command.LEAVE:
            return engine.leave_shop()
        if action == Command.BROWSE:
            return ActionResult(messages=[])
        return None


PHASE_STATES: dict[Phase, PhaseState] = {
    Phase.EXPLORING: ExploringPhaseState(),
    Phase.COMBAT: CombatPhaseState(),
    Phase.SHOP: ShopPhaseState(),
}
