from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dark_fort.game.enums import Command, ItemType, Phase
from dark_fort.game.models import ActionResult
from dark_fort.game.tables import SHOP_ITEMS

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
        self, engine: GameEngine, action: str
    ) -> ActionResult | None: ...


class ExploringPhaseState(PhaseState):
    phase = Phase.EXPLORING
    available_commands = [Command.EXPLORE, Command.INVENTORY]

    def handle_command(self, engine: GameEngine, action: str) -> ActionResult | None:
        if action == "explore":
            return engine.enter_new_room()
        if action == "inventory":
            player = engine.state.player
            if not player.inventory:
                return ActionResult(messages=["Your inventory is empty."])
            messages = ["Inventory:"]
            type_prefixes = {
                ItemType.WEAPON: "W",
                ItemType.ARMOR: "A",
                ItemType.POTION: "P",
                ItemType.SCROLL: "S",
                ItemType.ROPE: "R",
                ItemType.CLOAK: "C",
            }
            for i, item in enumerate(player.inventory):
                prefix = type_prefixes.get(item.type, "?")
                stats = item.display_stats()
                stats_str = f" ({stats})" if stats else ""
                messages.append(f"  {i + 1}. [{prefix}] {item.name}{stats_str}")
            return ActionResult(messages=messages)
        return None


class CombatPhaseState(PhaseState):
    phase = Phase.COMBAT
    available_commands = [Command.ATTACK, Command.FLEE, Command.USE_ITEM]

    def handle_command(self, engine: GameEngine, action: str) -> ActionResult | None:
        if action == "attack":
            return engine.attack()
        if action == "flee":
            return engine.flee()
        if action == "use_item":
            return ActionResult(messages=["Use item: (type item number)"])
        return None


class ShopPhaseState(PhaseState):
    phase = Phase.SHOP
    available_commands = [Command.BROWSE, Command.LEAVE]

    def handle_command(self, engine: GameEngine, action: str) -> ActionResult | None:
        if action == "leave":
            return engine.leave_shop()
        if action == "browse":
            messages = ["Available wares:"]
            for i, (item, price) in enumerate(SHOP_ITEMS):
                stats = item.display_stats()
                stats_str = f" ({stats})" if stats else ""
                messages.append(f"  {i + 1}. {item.name}{stats_str} — {price}s")
            messages.append(f"\nYour silver: {engine.state.player.silver}s")
            messages.append("Press 1-9, 0 for item 10, or L to leave.")
            return ActionResult(messages=messages)
        return None


PHASE_STATES: dict[Phase, PhaseState] = {
    Phase.EXPLORING: ExploringPhaseState(),
    Phase.COMBAT: CombatPhaseState(),
    Phase.SHOP: ShopPhaseState(),
}
