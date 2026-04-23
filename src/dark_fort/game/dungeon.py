from dark_fort.game.dice import roll
from dark_fort.game.models import Room
from dark_fort.game.tables import get_room_shape


class DungeonBuilder:
    """Builds rooms and their connections."""

    def __init__(self) -> None:
        self._counter = 0

    def build_room(self, is_entrance: bool = False) -> Room:
        room_id = self._counter
        self._counter += 1
        shape = get_room_shape(roll("d6") + roll("d6"))
        doors = roll("d4")
        return Room(
            id=room_id,
            shape=shape,
            doors=doors,
            result="pending",
            explored=is_entrance,
        )

    @staticmethod
    def connect(room_a: Room, room_b: Room) -> None:
        room_a.connections.append(room_b.id)
        room_b.connections.append(room_a.id)

    def build_dungeon(self, min_rooms: int = 12) -> list[Room]:
        rooms = [self.build_room(is_entrance=True)]
        while len(rooms) < min_rooms:
            room = self.build_room()
            parent = rooms[roll(f"d{len(rooms)}") - 1]
            self.connect(parent, room)
            rooms.append(room)
        return rooms
