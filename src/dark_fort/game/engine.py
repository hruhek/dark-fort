from __future__ import annotations

import random

from dark_fort.game.dice import roll
from dark_fort.game.dungeon import DungeonBuilder
from dark_fort.game.enums import EquipSlot, Phase
from dark_fort.game.models import (
    ActionResult,
    Armor,
    Cloak,
    CombatState,
    GameState,
    Potion,
    Room,
    Rope,
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
    ITEMS_TABLE,
    ROOM_RESULTS,
    SCROLLS_TABLE,
    SHOP_ITEMS,
    WEAK_MONSTERS,
    WEAPONS_TABLE,
)


def _get_benefit_name(number: int) -> str:
    from dark_fort.game.tables import LEVEL_BENEFITS

    return LEVEL_BENEFITS[number - 1]


class GameEngine:
    """Owns GameState and exposes methods for all game actions."""

    def __init__(self) -> None:
        self.state = GameState(phase=Phase.TITLE)
        self._dungeon = DungeonBuilder()

    @property
    def explored_count(self) -> int:
        return sum(1 for r in self.state.rooms.values() if r.explored)

    def start_game(self) -> ActionResult:
        """Generate entrance room and starting equipment."""
        self.state = GameState(phase=Phase.ENTRANCE)
        self._dungeon = DungeonBuilder()

        weapon, item = generate_starting_equipment()
        self.state.player.weapon = weapon
        self.state.player.silver = roll("d6") + 15

        match item:
            case Armor():
                self.state.player.armor = item
            case Potion() | Scroll():
                self.state.player.inventory.append(item)
            case Cloak():
                self.state.player.inventory.append(item)
                item.charges = roll("d4")

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

        match entrance_result:
            case 0:  # Find a random item
                item_roll = roll("d6") - 1
                match ITEMS_TABLE[item_roll]:
                    case "Random weapon":
                        random_item = random.choice(WEAPONS_TABLE)
                    case "Potion":
                        random_item = Potion(name="Potion", heal="d6")
                    case "Rope":
                        random_item = Rope(name="Rope")
                    case "Random scroll":
                        scroll_name, scroll_type, _ = random.choice(SCROLLS_TABLE)
                        random_item = Scroll(
                            name=f"Scroll: {scroll_name}", scroll_type=scroll_type
                        )
                    case "Armor":
                        random_item = Armor(name="Armor", absorb="d4")
                    case "Cloak of invisibility":
                        random_item = Cloak(name="Cloak of invisibility")
                    case _:
                        random_item = Potion(name="Potion", heal="d6")
                self.state.player.inventory.append(random_item)
                messages.append(f"You find a {random_item.name}.")
            case 1:  # A weak monster stands guard
                monster = random.choice(WEAK_MONSTERS)
                self.state.combat = CombatState(monster=monster, monster_hp=monster.hp)
                self.state.phase = Phase.COMBAT
                messages.append(f"A {monster.name} attacks!")
            case 2:  # A dying mystic gives a random scroll
                scroll_name, scroll_type, _ = random.choice(SCROLLS_TABLE)
                scroll = Scroll(name=f"Scroll: {scroll_name}", scroll_type=scroll_type)
                self.state.player.inventory.append(scroll)
                messages.append(f"The mystic gives you a {scroll.name}.")
            case _:  # Quiet — nothing
                pass

        if self.state.phase == Phase.ENTRANCE:
            self.state.phase = Phase.EXPLORING
        return ActionResult(messages=messages, phase=self.state.phase)

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

        result = resolve_room_event(room_result, self.state.player)
        messages.extend(result.messages)

        if result.combat:
            self.state.combat = result.combat
        if result.explored and self.state.current_room:
            self.state.current_room.explored = True
        if result.silver_delta:
            self.state.player.silver += result.silver_delta
        if result.hp_delta:
            self.state.player.hp += result.hp_delta

        final_phase = result.phase or Phase.EXPLORING
        self.state.phase = final_phase

        if final_phase == Phase.SHOP:
            self.state.shop_wares = list(SHOP_ITEMS)

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

        if index < 0 or index >= len(self.state.shop_wares):
            return ActionResult(messages=["Invalid item."])

        entry = self.state.shop_wares[index]
        item, price = entry.item, entry.price

        if self.state.player.silver < price:
            return ActionResult(
                messages=[
                    f"Not enough silver. Need {price}s, have {self.state.player.silver}s."
                ]
            )

        self.state.player.silver -= price

        match item.equip_slot:
            case EquipSlot.WEAPON:
                weapon = item
                if self.state.player.weapon is not None:
                    self.state.player.inventory.append(self.state.player.weapon)
                    msg = f"You buy {weapon.name} for {price}s. {self.state.player.weapon.name} moved to inventory."
                else:
                    msg = f"You buy {weapon.name} for {price}s."
                self.state.player.weapon = weapon  # ty: ignore[invalid-assignment]
            case EquipSlot.ARMOR:
                armor = item
                if self.state.player.armor is not None:
                    self.state.player.inventory.append(self.state.player.armor)
                    msg = f"You buy {armor.name} for {price}s. {self.state.player.armor.name} moved to inventory."
                else:
                    msg = f"You buy {armor.name} for {price}s."
                self.state.player.armor = armor  # ty: ignore[invalid-assignment]
            case EquipSlot.SPECIAL:
                if isinstance(item, Cloak):
                    self.state.player.inventory.append(item)
                    item.charges = roll("d4")
                    msg = f"You buy {item.name} for {price}s ({item.charges} charges)."
                else:
                    msg = f"You buy {item.name} for {price}s."
            case EquipSlot.NONE:
                if isinstance(item, Scroll):
                    from dark_fort.game.tables import SCROLLS_TABLE

                    scroll_name, scroll_type, _ = SCROLLS_TABLE[roll("d4") - 1]
                    self.state.player.inventory.append(
                        Scroll(name=scroll_name, scroll_type=scroll_type)
                    )
                    msg = f"You buy {scroll_name} for {price}s."
                else:
                    self.state.player.inventory.append(item)
                    msg = f"You buy {item.name} for {price}s."

        return ActionResult(messages=[msg])

    def leave_shop(self) -> ActionResult:
        """Leave the Void Peddler."""
        self.state.phase = Phase.EXPLORING
        self.state.shop_wares = []
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

    def save(self) -> dict:
        return {
            "state": self.state.snapshot(),
            "room_counter": self._dungeon._counter,
        }

    @classmethod
    def load(cls, data: dict) -> GameEngine:
        engine = cls.__new__(cls)
        engine.state = GameState.restore(data["state"])
        engine._dungeon = DungeonBuilder()
        engine._dungeon._counter = data["room_counter"]
        return engine

    def _generate_room(self, is_entrance: bool = False) -> Room:
        """Generate a new room via DungeonBuilder."""
        return self._dungeon.build_room(is_entrance=is_entrance)
