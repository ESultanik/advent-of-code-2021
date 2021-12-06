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
