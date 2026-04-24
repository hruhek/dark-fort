from __future__ import annotations

import random

from dark_fort.game.dice import roll
from dark_fort.game.models import Exit, Room
from dark_fort.game.tables import get_room_shape

DIRECTIONS = ["north", "south", "east", "west"]
OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}


class DungeonBuilder:
    """Builds rooms and their exits with cardinal directions."""

    def __init__(self) -> None:
        self._counter = 0
        self.rooms: dict[int, Room] = {}
        # (x, y) -> room_id for grid placement
        self._grid: dict[tuple[int, int], int] = {}

    def build_room(self, is_entrance: bool = False) -> Room:
        room_id = self._counter
        self._counter += 1
        shape = get_room_shape(roll("d6") + roll("d6"))
        return Room(
            id=room_id,
            shape=shape,
            result="pending",
            explored=is_entrance,
        )

    def build_dungeon(self, max_rooms: int = 20) -> list[Room]:
        """Generate a connected dungeon graph upfront."""
        self._max_rooms = max_rooms
        entrance = self.build_room(is_entrance=True)
        self.rooms[entrance.id] = entrance
        self._grid[(0, 0)] = entrance.id

        # Entrance gets d4 exits (1-4)
        num_exits = roll("d4")
        self._add_exits(entrance, num_exits)

        return list(self.rooms.values())

    def _add_exits(self, start_room: Room, count: int) -> None:
        """Add exits to a room, connecting to new or existing rooms."""
        stack: list[tuple[Room, int]] = [(start_room, count)]

        while stack:
            room, count = stack.pop()
            x, y = self._get_room_position(room.id)
            available = self._available_directions(x, y)
            # Only add as many exits as we have available directions
            count = min(count, len(available))
            if count == 0:
                continue
            directions = random.sample(available, count)

            for direction in directions:
                dx, dy = self._direction_delta(direction)
                new_x, new_y = x + dx, y + dy

                if (new_x, new_y) in self._grid:
                    # Connect to existing room
                    existing_id = self._grid[(new_x, new_y)]
                    self._connect(room, self.rooms[existing_id], direction)
                elif len(self.rooms) < self._max_rooms:
                    # Create new room (only if under cap)
                    new_room = self.build_room()
                    self.rooms[new_room.id] = new_room
                    self._grid[(new_x, new_y)] = new_room.id
                    self._connect(room, new_room, direction)
                    # New room gets 1 mandatory back exit + (d4-1) additional
                    additional = min(roll("d4") - 1, 2)
                    stack.append((new_room, additional))

    def _connect(self, room_a: Room, room_b: Room, direction: str) -> None:
        """Create bidirectional exits between two rooms."""
        room_a.exits.append(
            Exit(
                door_number=len(room_a.exits) + 1,
                destination=room_b.id,
                direction=direction,
            )
        )
        room_b.exits.append(
            Exit(
                door_number=len(room_b.exits) + 1,
                destination=room_a.id,
                direction=OPPOSITES[direction],
            )
        )

    def _get_room_position(self, room_id: int) -> tuple[int, int]:
        for pos, rid in self._grid.items():
            if rid == room_id:
                return pos
        raise ValueError(f"Room {room_id} not found on grid")

    def _available_directions(self, x: int, y: int) -> list[str]:
        """Return directions that don't have a room adjacent already."""
        available = []
        for direction in DIRECTIONS:
            dx, dy = self._direction_delta(direction)
            if (x + dx, y + dy) not in self._grid:
                available.append(direction)
        return available

    @staticmethod
    def _direction_delta(direction: str) -> tuple[int, int]:
        return {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
        }[direction]
