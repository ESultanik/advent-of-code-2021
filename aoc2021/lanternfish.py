from collections import Counter
from typing import List

from . import Challenge


class Lanternfish(Challenge):
    day = 6

    @Challenge.register_part(0)
    def simulation(self):
        with open(self.input_path, "r") as f:
            ages: List[int] = [int(age) for age in f.read().split(",")]
        for i in range(80):
            new_ages: List[int] = []
            for age in ages:
                if age == 0:
                    new_ages.extend([6, 8])
                else:
                    new_ages.append(age - 1)
            ages = new_ages
        self.output.write(f"{len(ages)}")

    @Challenge.register_part(1)
    def many_days(self):
        with open(self.input_path, "r") as f:
            ages = Counter([int(age) for age in f.read().split(",")])
        for i in range(256):
            new_ages = Counter()
            for age, num_fish in ages.items():
                if age == 0:
                    new_ages[6] += num_fish
                    new_ages[8] += num_fish
                else:
                    new_ages[age - 1] += num_fish
            ages = new_ages
        self.output.write(f"{sum(ages.values())}")
