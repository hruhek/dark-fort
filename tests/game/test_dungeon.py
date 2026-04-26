from dark_fort.game.dungeon import DungeonBuilder
from dark_fort.game.models import Room


class TestDungeonBuilder:
    def test_build_room_returns_room(self):
        builder = DungeonBuilder()
        room = builder.build_room()
        assert isinstance(room, Room)
        assert room.shape
        assert room.exits == []

    def test_build_room_increments_counter(self):
        builder = DungeonBuilder()
        room0 = builder.build_room()
        room1 = builder.build_room()
        assert room0.id == 0
        assert room1.id == 1

    def test_build_entrance_is_explored(self):
        builder = DungeonBuilder()
        room = builder.build_room(is_entrance=True)
        assert room.explored is True

    def test_build_non_entrance_is_unexplored(self):
        builder = DungeonBuilder()
        room = builder.build_room(is_entrance=False)
        assert room.explored is False

    def test_build_dungeon_first_room_is_entrance(self):
        builder = DungeonBuilder()
        rooms = builder.build_dungeon()
        assert rooms[0].explored is True

    def test_build_dungeon_rooms_are_connected(self):
        builder = DungeonBuilder()
        rooms = builder.build_dungeon()
        connected_ids: set[int] = set()
        for room in rooms:
            for exit in room.exits:
                connected_ids.add(exit.destination)
        # Every non-entrance room should be reachable from at least one other room
        non_entrance_ids = {r.id for r in rooms if not r.explored}
        for rid in non_entrance_ids:
            assert rid in connected_ids


def test_build_dungeon_creates_entrance():
    from dark_fort.game.dungeon import DungeonBuilder

    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    assert len(rooms) >= 1
    entrance = rooms[0]
    assert entrance.explored is True
    assert (
        len(entrance.exits) >= 1
    )  # entrance always has at least 1 door (d4=1 is minimum)


def test_build_dungeon_connectivity():
    from dark_fort.game.dungeon import DungeonBuilder

    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    for room in rooms:
        for exit in room.exits:
            dest = builder.rooms[exit.destination]
            assert any(e.destination == room.id for e in dest.exits)


def test_build_dungeon_directions():
    from dark_fort.game.dungeon import DungeonBuilder

    builder = DungeonBuilder()
    rooms = builder.build_dungeon()
    for room in rooms:
        for exit in room.exits:
            assert exit.direction in ["north", "south", "east", "west"]
