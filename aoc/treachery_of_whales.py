from typing import List, Optional

from . import Challenge


class TheTreacheryOfWhales(Challenge):
    day = 7

    @Challenge.register_part(0)
    def fuel(self):
        with open(self.input_path, "r") as f:
            positions: List[int] = [int(position) for position in f.read().split(",")]
        best_cost: Optional[int] = None
        for possibility in range(min(positions), max(positions) + 1):
            fuel_spent = sum(abs(p - possibility) for p in positions)
            if best_cost is None or fuel_spent < best_cost:
                best_cost = fuel_spent
        self.output.write(str(best_cost))
        self.output.write("\n")

    @staticmethod
    def increased_move_cost(distance: int) -> int:
        distance = abs(distance)
        return distance * (distance + 1) // 2

    @Challenge.register_part(1)
    def increased_cost(self):
        with open(self.input_path, "r") as f:
            positions: List[int] = [int(position) for position in f.read().split(",")]
        best_cost: Optional[int] = None
        for possibility in range(min(positions), max(positions) + 1):
            fuel_spent = sum(TheTreacheryOfWhales.increased_move_cost(p - possibility) for p in positions)
            if best_cost is None or fuel_spent < best_cost:
                best_cost = fuel_spent
        self.output.write(str(best_cost))
        self.output.write("\n")
