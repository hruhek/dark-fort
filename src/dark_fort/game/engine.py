from __future__ import annotations

from dark_fort.game.dice import roll
from dark_fort.game.enums import Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    GameState,
    Potion,
    Room,
    Scroll,
)
from dark_fort.game.rules import (
    apply_level_benefit,
    check_level_up,
    flee_combat,
    generate_starting_equipment,
    resolve_combat_hit,
    resolve_room_event,
)
from dark_fort.game.tables import (
    ENTRANCE_RESULTS,
    ROOM_RESULTS,
    SHOP_ITEMS,
    get_room_shape,
)


def _get_benefit_name(number: int) -> str:
    from dark_fort.game.tables import LEVEL_BENEFITS

    return LEVEL_BENEFITS[number - 1]


class GameEngine:
    """Owns GameState and exposes methods for all game actions."""

    def __init__(self) -> None:
        self.state = GameState(phase=Phase.TITLE)
        self._room_counter = 0

    @property
    def explored_count(self) -> int:
        return sum(1 for r in self.state.rooms.values() if r.explored)

    def start_game(self) -> ActionResult:
        """Generate entrance room and starting equipment."""
        self.state = GameState(phase=Phase.ENTRANCE)
        self._room_counter = 0

        weapon, item = generate_starting_equipment()
        self.state.player.weapon = weapon
        self.state.player.silver = roll("d6") + 15

        match item:
            case Armor():
                self.state.player.armor = item
            case Potion() | Scroll():
                self.state.player.inventory.append(item)
            case Cloak():
                self.state.player.cloak_charges = roll("d4")

        entrance = self._generate_room(is_entrance=True)
        self.state.current_room = entrance
        self.state.rooms[entrance.id] = entrance

        messages = [
            f"Your name is {self.state.player.name}.",
            f"HP: {self.state.player.hp}/{self.state.player.max_hp}",
            f"Silver: {self.state.player.silver}",
            f"You start with a {weapon.name} ({weapon.damage}).",
            "You enter the Dark Fort...",
        ]

        entrance_result = roll("d4") - 1
        entrance_msg = ENTRANCE_RESULTS[entrance_result]
        messages.append(entrance_msg)

        self.state.phase = Phase.EXPLORING
        return ActionResult(messages=messages, phase=Phase.EXPLORING)

    def enter_new_room(self) -> ActionResult:
        """Move to a new room through an unexplored door."""
        room = self._generate_room()
        self.state.current_room = room
        self.state.rooms[room.id] = room

        messages = [
            f"You enter a {room.shape.lower()} room with {room.doors} door(s).",
        ]

        room_result_idx = roll("d6") - 1
        room_result = ROOM_RESULTS[room_result_idx]

        result = resolve_room_event(self.state, room_result)
        messages.extend(result.messages)

        final_phase = result.phase or Phase.EXPLORING
        self.state.phase = final_phase

        return ActionResult(messages=messages, phase=final_phase)

    def attack(self, player_roll: int | None = None) -> ActionResult:
        """Attack the current monster."""
        if not self.state.combat:
            return ActionResult(messages=["No monster to attack."])

        result = resolve_combat_hit(self.state.player, self.state.combat, player_roll)

        if result.phase == Phase.GAME_OVER:
            self.state.phase = Phase.GAME_OVER
        elif result.phase == Phase.EXPLORING:
            self.state.combat = None
            if self.state.current_room:
                self.state.current_room.explored = True
            self.state.phase = Phase.EXPLORING

            if check_level_up(self.state):
                self.state.level_up_queue = True
                result.messages.append("You feel power coursing through you! Level up!")

        return result

    def flee(self, player_roll: int | None = None) -> ActionResult:
        """Flee from combat."""
        if not self.state.combat:
            return ActionResult(messages=["No monster to flee from."])

        result = flee_combat(self.state.player, player_roll)
        self.state.combat = None
        self.state.phase = result.phase or Phase.EXPLORING
        return result

    def buy_item(self, index: int) -> ActionResult:
        """Buy an item from the Void Peddler."""
        if self.state.phase != Phase.SHOP:
            return ActionResult(messages=["The shop is not open."])

        if index < 0 or index >= len(SHOP_ITEMS):
            return ActionResult(messages=["Invalid item."])

        entry = SHOP_ITEMS[index]
        item, price = entry.item, entry.price

        if self.state.player.silver < price:
            return ActionResult(
                messages=[
                    f"Not enough silver. Need {price}s, have {self.state.player.silver}s."
                ]
            )

        self.state.player.silver -= price

        match item:
            case Armor():
                if self.state.player.armor is not None:
                    self.state.player.inventory.append(self.state.player.armor)
                    msg = f"You buy {item.name} for {price}s. {self.state.player.armor.name} moved to inventory."
                else:
                    msg = f"You buy {item.name} for {price}s."
                self.state.player.armor = item
            case Cloak():
                self.state.player.cloak_charges = roll("d4")
                msg = f"You buy {item.name} for {price}s ({self.state.player.cloak_charges} charges)."
            case Scroll():
                from dark_fort.game.tables import SCROLLS_TABLE

                scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
                self.state.player.inventory.append(
                    Scroll(name=scroll_name, scroll_type=scroll_type)
                )
                msg = f"You buy {scroll_name} for {price}s."
            case _:
                self.state.player.inventory.append(item)
                msg = f"You buy {item.name} for {price}s."

        return ActionResult(messages=[msg])

    def leave_shop(self) -> ActionResult:
        """Leave the Void Peddler."""
        self.state.phase = Phase.EXPLORING
        if self.state.current_room:
            self.state.current_room.explored = True
        return ActionResult(
            messages=["You leave the Void Peddler."], phase=Phase.EXPLORING
        )

    def use_item(self, index: int) -> ActionResult:
        """Use an item from inventory."""
        if index < 0 or index >= len(self.state.player.inventory):
            return ActionResult(messages=["Invalid item index."])

        item = self.state.player.inventory[index]
        return item.use(self.state, index)

    def check_game_over(self) -> ActionResult:
        """Check if the player is dead."""
        if self.state.player.hp <= 0:
            self.state.phase = Phase.GAME_OVER
            return ActionResult(messages=["You have fallen."], phase=Phase.GAME_OVER)
        return ActionResult(messages=[])

    def check_victory(self) -> ActionResult:
        """Check if all level benefits have been claimed."""
        if len(self.state.player.level_benefits) >= 6:
            self.state.phase = Phase.VICTORY
            return ActionResult(
                messages=["You retire until the 7th Misery. Congratulations!"],
                phase=Phase.VICTORY,
            )
        return ActionResult(messages=[])

    def level_up(self, benefit_number: int) -> ActionResult:
        """Apply a level-up benefit."""
        if benefit_number < 1 or benefit_number > 6:
            return ActionResult(messages=["Invalid benefit number."])

        if benefit_number in self.state.player.level_benefits:
            return ActionResult(messages=["You already claimed this benefit."])

        apply_level_benefit(benefit_number, self.state.player)
        self.state.player.level_benefits.append(benefit_number)

        messages = [f"Benefit: {_get_benefit_name(benefit_number)}"]

        if len(self.state.player.level_benefits) >= 6:
            messages.append("All benefits claimed! You retire victorious!")
            self.state.phase = Phase.VICTORY
            return ActionResult(messages=messages, phase=Phase.VICTORY)

        self.state.level_up_queue = False
        return ActionResult(messages=messages)

    def _generate_room(self, is_entrance: bool = False) -> Room:
        """Generate a new room with shape, doors, and connections."""
        room_id = self._room_counter
        self._room_counter += 1

        shape_roll = roll("d6") + roll("d6")
        shape = get_room_shape(shape_roll)

        doors = roll("d4")

        return Room(
            id=room_id,
            shape=shape,
            doors=doors,
            result="pending",
            explored=False,
        )
