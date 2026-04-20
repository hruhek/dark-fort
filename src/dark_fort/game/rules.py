from dark_fort.game.dice import chance_in_6, roll
from dark_fort.game.enums import ItemType, Phase
from dark_fort.game.models import (
    ActionResult,
    CombatState,
    GameState,
    Item,
    Monster,
    Player,
    Weapon,
)
from dark_fort.game.tables import (
    SCROLLS_TABLE,
    WEAPONS_TABLE,
    get_weak_monster,
)


def generate_starting_equipment() -> tuple[Weapon, Item]:
    """Roll 1d4 on weapon table and 1d4 on item table."""
    weapon_idx = roll("d4") - 1
    item_idx = roll("d4") - 1

    weapon = WEAPONS_TABLE[weapon_idx]

    item_table = [
        Item(name="Armor", type=ItemType.ARMOR),
        Item(name="Potion", type=ItemType.POTION, damage="d6"),
        Item(name="Scroll: Summon weak daemon", type=ItemType.SCROLL),
        Item(name="Cloak of invisibility", type=ItemType.CLOAK),
    ]
    item = item_table[item_idx]

    return weapon, item


def resolve_combat_hit(
    player: Player, combat: CombatState, player_roll: int | None = None
) -> ActionResult:
    """Resolve one combat round. Returns ActionResult with messages."""
    if player_roll is None:
        player_roll = roll("d6")

    monster = combat.monster
    messages: list[str] = []

    effective_roll = player_roll + player.attack_bonus

    if combat.daemon_assist and player.daemon_fights_remaining > 0:
        messages.append("Your daemon attacks alongside you!")
        effective_roll += roll("d4")

    messages.append(
        f"Rolling to hit... you rolled {player_roll} (+{player.attack_bonus} bonus)"
    )

    if effective_roll >= monster.points:
        messages.append(f"HIT! (needed {monster.points})")

        if player.weapon:
            damage = roll(player.weapon.damage)
            messages.append(f"You deal {damage} damage with {player.weapon.name}")
        else:
            damage = roll("d4-1")
            messages.append(f"You deal {damage} damage (unarmed)")

        combat.monster_hp -= damage

        if combat.monster_hp <= 0:
            messages.append(f"{monster.name} is slain!")
            messages.append(f"You gain {monster.points} points")
            player.points += monster.points
            combat.monster_hp = 0
            _resolve_loot(monster, player, messages)

            if monster.special == "7_points_on_kill":
                messages.append("The troll crumbles to dust — 7 points earned!")
                player.points = max(0, player.points - monster.points) + 7
    else:
        messages.append(f"MISS! (rolled {effective_roll}, needed {monster.points})")
        messages.append(f"{monster.name} attacks you!")

        monster_dmg = roll(monster.damage)
        messages.append(f"{monster.name} deals {monster_dmg} damage")

        if player.armor:
            absorbed = roll("d4")
            monster_dmg = max(0, monster_dmg - absorbed)
            messages.append(f"Armor absorbs {absorbed} damage")

        player.hp -= monster_dmg
        messages.append(
            f"You take {monster_dmg} damage (HP: {player.hp}/{player.max_hp})"
        )

        if monster.special:
            special_roll = roll("d6")
            special_result = resolve_monster_special(monster, special_roll)
            if special_result:
                messages.append(special_result)

    combat.player_turns += 1

    if player.hp <= 0:
        messages.append("You have fallen!")
        return ActionResult(messages=messages, phase=Phase.GAME_OVER)

    if combat.monster_hp <= 0:
        return ActionResult(messages=messages, phase=Phase.EXPLORING)

    return ActionResult(messages=messages)


def _resolve_loot(monster: Monster, player: Player, messages: list[str]) -> None:
    """Handle monster loot drops."""
    if monster.special == "loot_dagger_2_in_6" and chance_in_6(2):
        player.inventory.append(
            Item(name="Dagger", type=ItemType.WEAPON, damage="d4", attack_bonus=1)
        )
        messages.append("Loot: Dagger")
    elif monster.special == "loot_scroll_2_in_6" and chance_in_6(2):
        scroll_name, _, _ = SCROLLS_TABLE[roll("d4") - 1]
        player.inventory.append(Item(name=scroll_name, type=ItemType.SCROLL))
        messages.append("Loot: Random scroll")
    elif monster.special == "loot_rope_2_in_6" and chance_in_6(2):
        player.inventory.append(Item(name="Rope", type=ItemType.ROPE))
        messages.append("Loot: Rope")


def resolve_monster_special(monster: Monster, special_roll: int) -> str | None:
    """Check if a monster's special ability triggers. Returns message or None."""
    if monster.special == "death_ray_1_in_6" and special_roll == 1:
        return "The Necro-Sorcerer's death ray strikes! You are transformed into a maggot. GAME OVER."
    if monster.special == "petrify_1_in_6" and special_roll == 1:
        return "Medusa's gaze petrifies you! GAME OVER."
    if monster.special == "instant_level_up_2_in_6" and special_roll <= 2:
        return "The Basilisk's power surges through you! Instant level up!"
    return None


def flee_combat(player: Player, player_roll: int | None = None) -> ActionResult:
    """Flee from combat, taking d4 damage."""
    if player_roll is None:
        player_roll = roll("d4")

    player.hp -= player_roll
    messages = [
        f"You flee! Taking {player_roll} damage (HP: {player.hp}/{player.max_hp})"
    ]

    if player.hp <= 0:
        messages.append("You have fallen!")
        return ActionResult(messages=messages, phase=Phase.GAME_OVER)

    return ActionResult(messages=messages, phase=Phase.EXPLORING)


def check_level_up(state: GameState) -> bool:
    """Check if player meets level-up conditions."""
    explored_count = sum(1 for r in state.rooms.values() if r.explored)
    return explored_count >= 12 and state.player.points >= 15


def apply_level_benefit(benefit_number: int, player: Player) -> None:
    """Apply a level-up benefit (1-indexed)."""
    if benefit_number == 2:
        player.attack_bonus += 1
    elif benefit_number == 3:
        player.max_hp = 20
        player.hp = min(player.hp + 5, player.max_hp)
    elif benefit_number == 4:
        for _ in range(5):
            player.inventory.append(
                Item(name="Potion", type=ItemType.POTION, damage="d6")
            )
    elif benefit_number == 5:
        player.inventory.append(
            Item(name="Mighty Zweihänder", type=ItemType.WEAPON, damage="d6+2")
        )


def resolve_pit_trap(player: Player, dice_roll: int | None = None) -> ActionResult:
    """Resolve a pit trap. Rope gives +1 to the d6 roll."""
    if dice_roll is None:
        dice_roll = roll("d6")

    rope_bonus = 1 if has_rope(player) else 0
    effective_roll = dice_roll + rope_bonus

    messages = [
        f"Pit trap! You rolled {dice_roll}"
        + (f" (+1 rope = {effective_roll})" if rope_bonus else "")
    ]

    if effective_roll <= 3:
        damage = roll("d6")
        player.hp -= damage
        messages.append(
            f"You fall in and take {damage} damage (HP: {player.hp}/{player.max_hp})"
        )
        if player.hp <= 0:
            messages.append("You have fallen!")
            return ActionResult(messages=messages, phase=Phase.GAME_OVER)
    else:
        messages.append("You avoid the trap safely.")

    return ActionResult(messages=messages)


def resolve_room_event(
    state: GameState, room_result: str, dice_roll: int | None = None
) -> ActionResult:
    """Resolve a room table result."""
    messages: list[str] = []
    phase = None

    if room_result == "Nothing. Explored.":
        messages.append("The room is empty. You mark it as explored.")
        if state.current_room:
            state.current_room.explored = True

    elif room_result == "Pit trap":
        pit_result = resolve_pit_trap(state.player, dice_roll)
        messages.extend(pit_result.messages)
        if pit_result.phase:
            phase = pit_result.phase
        if state.current_room and not phase:
            state.current_room.explored = True

    elif room_result == "Riddling Soothsayer":
        if dice_roll is None:
            dice_roll = roll("d6")
        if dice_roll % 2 == 1:
            messages.append("The Soothsayer rewards you! Gain 10 silver or 3 points.")
            state.player.silver += 10
            messages.append("You gain 10 silver.")
        else:
            damage = roll("d4")
            state.player.hp -= damage
            messages.append(
                f"The Soothsayer curses you! Take {damage} damage (ignores armor)."
            )
            if state.player.hp <= 0:
                messages.append("You have fallen!")
                phase = Phase.GAME_OVER
        if state.current_room and not phase:
            state.current_room.explored = True

    elif room_result == "Weak monster":
        monster = get_weak_monster(roll("d4") - 1)
        state.combat = CombatState(monster=monster, monster_hp=monster.hp)
        messages.append(f"A {monster.name} stands guard! Attack!")
        phase = Phase.COMBAT

    elif room_result == "Tough monster":
        from dark_fort.game.tables import get_tough_monster

        monster = get_tough_monster(roll("d4") - 1)
        state.combat = CombatState(monster=monster, monster_hp=monster.hp)
        messages.append(f"A {monster.name} blocks your path! Attack!")
        phase = Phase.COMBAT

    elif room_result == "Void Peddler":
        messages.append("You encounter the Void Peddler. Wares are displayed.")
        phase = Phase.SHOP

    return ActionResult(messages=messages, phase=phase)


def has_rope(player: Player) -> bool:
    return any(item.type == ItemType.ROPE for item in player.inventory)
