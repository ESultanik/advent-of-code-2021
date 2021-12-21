import re
from typing import Iterable, Tuple

from . import Challenge


class DeterministicDice:
    def __init__(self):
        self.value: int = 1
        self.num_rolls: int = 0

    def __iter__(self):
        return self

    def __next__(self) -> int:
        self.num_rolls += 1
        result = self.value
        self.value = (self.value % 100) + 1
        return result


class DiracDice(Challenge):
    day = 21

    @Challenge.register_part(0)
    def deterministic(self):
        # with open(self.input_path, "r") as f:
        #     positions: List[int] = [int(position) for position in f.read().split(",")]
        positions = [6, 8]
        scores = [0, 0]
        die = DeterministicDice()
        player = 0
        while not any(score >= 1000 for score in scores):
            r1, r2, r3 = (next(die) for _ in range(3))
            move = r1 + r2 + r3
            positions[player] = ((positions[player] - 1 + move) % 10) + 1
            scores[player] += positions[player]
            print(f"Player {player + 1} rolls {r1}+{r2}+{r3} and moves to space {positions[player]} for a total score "
                  f"of {scores[player]}")
            player = (player + 1) % len(positions)
        losing_score = min(scores)
        self.output.write(f"{losing_score * die.num_rolls}")
