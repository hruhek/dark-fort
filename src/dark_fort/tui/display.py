from dark_fort.game.enums import ItemType
from dark_fort.game.models import GameState

TYPE_PREFIXES: dict[ItemType, str] = {
    ItemType.WEAPON: "W",
    ItemType.ARMOR: "A",
    ItemType.POTION: "P",
    ItemType.SCROLL: "S",
    ItemType.ROPE: "R",
    ItemType.CLOAK: "C",
}

# TODO:
def format_inventory(state: GameState) -> list[str]:
    player = state.player
    if not player.inventory:
        return ["Your inventory is empty."]
    lines = ["Inventory:"]
    for i, item in enumerate(player.inventory):
        prefix = TYPE_PREFIXES.get(item.type, "?")
        stats = item.display_stats()
        stats_str = f" ({stats})" if stats else ""
        lines.append(f"  {i + 1}. [{prefix}] {item.name}{stats_str}")
    return lines


def format_shop_wares(state: GameState) -> list[str]:
    lines = ["Available wares:"]
    for i, entry in enumerate(state.shop_wares):
        lines.append(f"  {i + 1}. {entry.display_stats()}")
    lines.append(f"\nYour silver: {state.player.silver}s")
    lines.append("Press 1-9, 0 for item 10, or L to leave.")
    return lines
