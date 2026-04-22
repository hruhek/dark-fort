import random
import re


def roll(expression: str) -> int:
    """Evaluate a dice expression and return the result.

    Supported formats:
        dN        — single die (e.g. d6, d4)
        dN+M      — die with modifier (e.g. d6+1, d6+2)
        dN-M      — die with negative modifier (e.g. d4-1)
        NdN       — multiple dice (e.g. 3d6)
        dN×dM     — multiply two dice (e.g. d4×d6)
    """
    if "×" in expression:
        parts = expression.split("×")
        return roll(parts[0]) * roll(parts[1])

    multi_match = re.match(r"^(\d+)d(\d+)$", expression)
    if multi_match:
        count = int(multi_match.group(1))
        sides = int(multi_match.group(2))
        return sum(random.randint(1, sides) for _ in range(count))

    mod_match = re.match(r"^d(\d+)([+-]\d+)$", expression)
    if mod_match:
        sides = int(mod_match.group(1))
        modifier = int(mod_match.group(2))
        return random.randint(1, sides) + modifier

    single_match = re.match(r"^d(\d+)$", expression)
    if single_match:
        sides = int(single_match.group(1))
        return random.randint(1, sides)

    raise ValueError(f"Unknown dice expression: {expression}")


def chance_in_6(chance: int) -> bool:
    """Return True with X-in-6 probability."""
    return random.randint(1, 6) <= chance
