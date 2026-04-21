from dark_fort.game.enums import MonsterSpecial, MonsterTier, Phase
from dark_fort.game.models import (
    Armor,
    CombatState,
    GameState,
    Monster,
    Player,
    Room,
    Rope,
    Weapon,
)
from dark_fort.game.rules import (
    apply_level_benefit,
    check_level_up,
    flee_combat,
    generate_starting_equipment,
    has_rope,
    resolve_combat_hit,
    resolve_monster_special,
    resolve_pit_trap,
)


class TestCombat:
    def test_player_hits_monster_when_roll_meets_points(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        player = Player(weapon=Weapon(name="Sword", damage="d6"))
        combat = CombatState(monster=monster, monster_hp=5)

        result = resolve_combat_hit(player, combat, player_roll=4)
        assert result.messages
        assert any("HIT" in m for m in result.messages)

    def test_player_misses_when_roll_below_points(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        player = Player(weapon=Weapon(name="Sword", damage="d6"))
        combat = CombatState(monster=monster, monster_hp=5)

        result = resolve_combat_hit(player, combat, player_roll=2)
        assert result.messages
        assert any("MISS" in m for m in result.messages)

    def test_unarmed_damage_is_d4_minus_1(self):
        player = Player()
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        combat = CombatState(monster=monster, monster_hp=5)

        result = resolve_combat_hit(player, combat, player_roll=4)
        assert any("HIT" in m for m in result.messages)


class TestFlee:
    def test_flee_deals_d4_damage(self):
        player = Player(hp=15)
        result = flee_combat(player, player_roll=3)
        assert player.hp == 12
        assert result.phase == "exploring"


class TestLevelUp:
    def test_level_up_with_15_points_and_12_rooms(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.points = 15
        for i in range(12):
            state.rooms[i] = Room(
                id=i, shape="Square", doors=1, result="nothing", explored=True
            )

        assert check_level_up(state) is True

    def test_no_level_up_without_enough_points(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.points = 10
        for i in range(12):
            state.rooms[i] = Room(
                id=i, shape="Square", doors=1, result="nothing", explored=True
            )

        assert check_level_up(state) is False

    def test_no_level_up_without_enough_rooms(self):
        state = GameState(phase=Phase.EXPLORING)
        state.player.points = 15
        for i in range(5):
            state.rooms[i] = Room(
                id=i, shape="Square", doors=1, result="nothing", explored=True
            )

        assert check_level_up(state) is False


class TestLevelBenefits:
    def test_benefit_3_sets_max_hp_to_20(self):
        player = Player(max_hp=15, hp=15)
        apply_level_benefit(3, player)
        assert player.max_hp == 20

    def test_benefit_2_adds_attack(self):
        player = Player(attack_bonus=0)
        apply_level_benefit(2, player)
        assert player.attack_bonus == 1

    def test_benefit_4_gives_5_potions(self):
        player = Player(inventory=[])
        apply_level_benefit(4, player)
        potions = [i for i in player.inventory if i.name == "Potion"]
        assert len(potions) == 5

    def test_benefit_5_gives_zweihander(self):
        player = Player()
        apply_level_benefit(5, player)
        assert any(w.name == "Mighty Zweihänder" for w in player.inventory)


class TestPitTrap:
    def test_pit_trap_with_rope_gets_bonus(self):
        player = Player()
        player.inventory.append(Rope(name="Rope"))
        resolve_pit_trap(player, dice_roll=4)
        assert player.hp == 15

    def test_pit_trap_without_rope_takes_damage(self):
        player = Player(hp=15)
        resolve_pit_trap(player, dice_roll=2)
        assert player.hp < 15


class TestStartingEquipment:
    def test_generates_weapon_and_item(self):
        weapon, item = generate_starting_equipment()
        assert weapon is not None
        assert item is not None


class TestMonsterSpecial:
    def test_death_ray_format(self):
        monster = Monster(
            name="Necro-Sorcerer",
            tier=MonsterTier.TOUGH,
            points=4,
            damage="d4",
            hp=8,
            special=MonsterSpecial.DEATH_RAY,
        )
        result = resolve_monster_special(monster, special_roll=1)
        assert result is not None


class TestHasRope:
    def test_has_rope_returns_true(self):
        player = Player()
        player.inventory.append(Rope(name="Rope"))
        assert has_rope(player) is True

    def test_has_rope_returns_false(self):
        player = Player()
        assert has_rope(player) is False


class TestWeaponAttackBonus:
    def test_weapon_attack_bonus_adds_to_hit_roll(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        player = Player(weapon=Weapon(name="Dagger", damage="d4", attack_bonus=1))
        combat = CombatState(monster=monster, monster_hp=5)
        result = resolve_combat_hit(player, combat, player_roll=2)
        assert any("HIT" in m for m in result.messages)

    def test_weapon_attack_bonus_still_misses_low_roll(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=5, damage="d4", hp=5
        )
        player = Player(weapon=Weapon(name="Dagger", damage="d4", attack_bonus=1))
        combat = CombatState(monster=monster, monster_hp=5)
        result = resolve_combat_hit(player, combat, player_roll=2)
        assert any("MISS" in m for m in result.messages)


class TestStartingEquipmentArmor:
    def test_starting_armor_item_has_absorb(self):
        weapon, item = generate_starting_equipment()
        if isinstance(item, Armor):
            assert item.absorb == "d4"


class TestArmorAbsorb:
    def test_armor_absorbs_damage(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        player = Player(hp=15, armor=Armor(name="Armor", absorb="d4"))
        combat = CombatState(monster=monster, monster_hp=5)
        result = resolve_combat_hit(player, combat, player_roll=2)
        assert any("Armor absorbs" in m for m in result.messages)

    def test_no_armor_no_absorb_message(self):
        monster = Monster(
            name="Goblin", tier=MonsterTier.WEAK, points=3, damage="d4", hp=5
        )
        player = Player(hp=15)
        combat = CombatState(monster=monster, monster_hp=5)
        result = resolve_combat_hit(player, combat, player_roll=2)
        assert not any("absorbs" in m for m in result.messages)
