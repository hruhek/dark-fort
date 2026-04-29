from __future__ import annotations

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
    Scroll,
)
from dark_fort.game.rules import (
    apply_level_benefit,
    check_level_up,
    flee_combat,
    generate_starting_equipment,
    resolve_combat_hit,
    resolve_entrance_event,
    resolve_room_event,
)
from dark_fort.game.tables import (
    ENTRANCE_RESULTS,
    LEVEL_BENEFITS,
    ROOM_RESULTS,
    SHOP_ITEMS,
    WEAK_MONSTERS,
    roll_on_table,
)


class GameEngine:
    """Owns GameState and exposes methods for all game actions."""

    def __init__(self) -> None:
        self.state = GameState(phase=Phase.TITLE)
        self._dungeon = DungeonBuilder()

    @property
    def explored_count(self) -> int:
        return sum(1 for r in self.state.rooms.values() if r.explored)

    def start_game(self) -> ActionResult:
        """Generate dungeon upfront and starting equipment."""
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

        # Build dungeon upfront
        rooms = self._dungeon.build_dungeon()
        for room in rooms:
            self.state.rooms[room.id] = room

        entrance = rooms[0]
        self.state.current_room = entrance

        messages = [
            f"Your name is {self.state.player.name}.",
            f"HP: {self.state.player.hp}/{self.state.player.max_hp}",
            f"Silver: {self.state.player.silver}",
            f"You start with a {weapon.name} ({weapon.damage}).",
            "You enter the Dark Fort...",
        ]

        if self.state.current_room:
            messages.extend(self.get_room_summary())

        entrance_event = roll_on_table(ENTRANCE_RESULTS, "d4")
        result = resolve_entrance_event(entrance_event, self.state.player)
        messages.extend(result.messages)

        if result.combat:
            self.state.combat = result.combat
        if result.phase:
            self.state.phase = result.phase

        if self.state.phase == Phase.ENTRANCE:
            self.state.phase = Phase.EXPLORING

        return ActionResult(messages=messages, phase=self.state.phase)

    def move_to_room(self, room_id: int) -> ActionResult:
        """Move to an existing room through an exit."""
        room = self.state.rooms.get(room_id)
        if not room:
            return ActionResult(messages=["That exit leads nowhere."])

        self.state.current_room = room

        if not room.explored and room.result == "pending":
            room_result = roll_on_table(ROOM_RESULTS, "d6")

            result = resolve_room_event(room_result, self.state.player)

            messages = [f"You enter a {room.shape.lower()} room."]

            if result.combat:
                self.state.combat = result.combat
                messages.extend(result.messages)
                self.state.phase = Phase.COMBAT
                return ActionResult(messages=messages, phase=Phase.COMBAT)

            if result.phase == Phase.SHOP:
                self.state.shop_wares = list(SHOP_ITEMS)
                messages.extend(result.messages)
                self.state.phase = Phase.SHOP
                return ActionResult(messages=messages, phase=Phase.SHOP)

            messages.extend(result.messages)

            if result.explored:
                room.explored = True
            if result.silver_delta:
                self.state.player.silver += result.silver_delta
            if result.hp_delta:
                self.state.player.hp += result.hp_delta

            final_phase = result.phase or Phase.EXPLORING
            self.state.phase = final_phase

            if final_phase == Phase.GAME_OVER:
                return ActionResult(messages=messages, phase=Phase.GAME_OVER)

            messages.extend(self.get_room_summary())
            return ActionResult(messages=messages, phase=self.state.phase)
        else:
            room.explored = True
            encounter_roll = roll("d4")
            if encounter_roll == 1:
                monster = roll_on_table(WEAK_MONSTERS, "d4")
                self.state.combat = CombatState(monster=monster, monster_hp=monster.hp)
                self.state.phase = Phase.COMBAT
                return ActionResult(
                    messages=[f"A {monster.name} springs from the shadows!"],
                    phase=Phase.COMBAT,
                )
            return ActionResult(messages=self.get_room_summary(), phase=Phase.EXPLORING)

    def get_room_exits(self) -> list[str]:
        """Return formatted exit descriptions for the current room."""
        if not self.state.current_room:
            return []

        room = self.state.current_room
        lines: list[str] = []
        for exit in room.exits:
            dest = self.state.rooms.get(exit.destination)
            if dest and dest.explored:
                status = f"Explored ({dest.shape})"
            else:
                status = "Unexplored"
            lines.append(
                f"  {exit.door_number}. {exit.direction.capitalize()} → {status}"
            )
        # Entrance room always has a dungeon exit
        if room.id == 0:
            lines.append("  0. Exit Dungeon")
        return lines

    def get_room_summary(self) -> list[str]:
        """Return room description + exit lines for the current room."""
        if not self.state.current_room:
            return []
        room = self.state.current_room
        status = "Explored" if room.explored else "Unexplored"
        return [
            f"You are in a {room.shape.lower()} room — {status}",
            *self.get_room_exits(),
        ]

    def exit_dungeon(self, give_silver: bool = False) -> ActionResult:
        """Exit the dungeon from the entrance room."""
        if not self.state.current_room or self.state.current_room.id != 0:
            return ActionResult(messages=["You can only exit from the entrance room."])

        if self.state.level_up_queue:
            messages = [
                "You leave the Dark Fort, ready to level up!",
                "Choose a benefit (1-6):",
            ]
            for i, name in enumerate(LEVEL_BENEFITS, 1):
                if i not in self.state.player.level_benefits:
                    messages.append(f"  {i}. {name}")
            self.state.phase = Phase.LEVEL_UP
            return ActionResult(messages=messages, phase=Phase.LEVEL_UP)

        explored = self.explored_count
        if self.state.player.silver >= 40 and explored >= 12:
            if give_silver:
                self.state.player.silver -= 40
                self.state.level_up_queue = True
                messages = [
                    "You give 40 silver to the poor of ruined Wästland.",
                    "You feel power coursing through you! Level up!",
                    "Choose a benefit (1-6):",
                ]
                for i, name in enumerate(LEVEL_BENEFITS, 1):
                    if i not in self.state.player.level_benefits:
                        messages.append(f"  {i}. {name}")
                self.state.phase = Phase.LEVEL_UP
                return ActionResult(messages=messages, phase=Phase.LEVEL_UP)
            messages = [
                f"You have {self.state.player.silver}s. Give 40 silver to the poor of ruined Wästland to level up? (Press G to give, or 0 to leave)",
            ]
            return ActionResult(messages=messages)

        messages = ["You leave the Dark Fort."]
        return ActionResult(messages=messages)

    def attack(self, player_roll: int | None = None) -> ActionResult:
        """Attack the current monster."""
        if not self.state.combat:
            return ActionResult(messages=["No monster to attack."])

        queued_before = self.state.level_up_queue
        points_before = self.state.player.points

        result = resolve_combat_hit(self.state.player, self.state.combat, player_roll)

        if result.phase == Phase.GAME_OVER:
            self.state.phase = Phase.GAME_OVER
        elif result.phase == Phase.EXPLORING:
            self.state.combat = None
            if self.state.current_room:
                self.state.current_room.explored = True
            self.state.phase = Phase.EXPLORING

            if queued_before:
                self.state.player.points = points_before
                result.messages.append("Return to the entrance room to level up!")

            if check_level_up(self.state) and not queued_before:
                self.state.level_up_queue = True
                result.messages.append(
                    "You feel power coursing through you! Return to the entrance to level up!"
                )

            result.messages.extend(self.get_room_summary())

        return result

    def flee(self, player_roll: int | None = None) -> ActionResult:
        """Flee from combat."""
        if not self.state.combat:
            return ActionResult(messages=["No monster to flee from."])

        result = flee_combat(self.state.player, player_roll)
        self.state.combat = None
        self.state.phase = result.phase or Phase.EXPLORING
        if self.state.phase == Phase.EXPLORING:
            result.messages.extend(self.get_room_summary())
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

                    scroll_name, scroll_type, _ = roll_on_table(SCROLLS_TABLE, "d4")
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
        messages = ["You leave the Void Peddler."]
        messages.extend(self.get_room_summary())
        return ActionResult(messages=messages, phase=Phase.EXPLORING)

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

        messages = [f"Benefit: {LEVEL_BENEFITS[benefit_number - 1]}"]

        if len(self.state.player.level_benefits) >= 6:
            messages.append("All benefits claimed! You retire victorious!")
            self.state.phase = Phase.VICTORY
            return ActionResult(messages=messages, phase=Phase.VICTORY)

        self.state.level_up_queue = False
        self.state.phase = Phase.EXPLORING
        messages.append("You return to the Dark Fort, stronger than before.")
        messages.extend(self.get_room_summary())
        return ActionResult(messages=messages, phase=Phase.EXPLORING)

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
