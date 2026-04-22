from dark_fort.game.dice import chance_in_6, roll


class TestRoll:
    def test_roll_single_die_returns_int(self):
        result = roll("d6")
        assert isinstance(result, int)

    def test_roll_d4_range(self):
        for _ in range(100):
            result = roll("d4")
            assert 1 <= result <= 4

    def test_roll_d6_range(self):
        for _ in range(100):
            result = roll("d6")
            assert 1 <= result <= 6

    def test_roll_d6_plus_1_range(self):
        for _ in range(100):
            result = roll("d6+1")
            assert 2 <= result <= 7

    def test_roll_d6_plus_2_range(self):
        for _ in range(100):
            result = roll("d6+2")
            assert 3 <= result <= 8

    def test_roll_3d6_range(self):
        for _ in range(100):
            result = roll("3d6")
            assert 3 <= result <= 18

    def test_roll_d4_times_d6_range(self):
        for _ in range(100):
            result = roll("d4×d6")
            assert 1 <= result <= 24

    def test_roll_d4_minus_1_range(self):
        for _ in range(100):
            result = roll("d4-1")
            assert 0 <= result <= 3


class TestChanceIn6:
    def test_chance_in_6_always_succeeds_at_6(self):
        for _ in range(100):
            assert chance_in_6(6) is True

    def test_chance_in_6_never_succeeds_at_0(self):
        for _ in range(100):
            assert chance_in_6(0) is False

    def test_chance_in_6_1_in_6_probability(self):
        successes = sum(chance_in_6(1) for _ in range(1000))
        assert 100 <= successes <= 250

    def test_chance_in_6_2_in_6_probability(self):
        successes = sum(chance_in_6(2) for _ in range(1000))
        assert 250 <= successes <= 450
