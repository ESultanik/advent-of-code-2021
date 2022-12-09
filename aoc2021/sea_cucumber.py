from pathlib import Path
from typing import List

from . import Challenge


class Trench:
    def __init__(self, cucumbers: List[List[str]]):
        self.cucumbers: List[List[str]] = cucumbers
        self.num_steps: int = 0

    def step(self) -> bool:
        changed = False
        for row in self.cucumbers:
            from_col = 0
            num_cols = len(row)
            final_col = num_cols
            while from_col < final_col:
                to_col = (from_col + 1) % num_cols
                if row[from_col] == ">" and row[to_col] == ".":
                    row[to_col] = row[from_col]
                    row[from_col] = "."
                    changed = True
                    if from_col == 0:
                        final_col -= 1
                    from_col += 1
                from_col += 1
        num_rows = len(self.cucumbers)
        for col in range(len(self.cucumbers[0])):
            final_row = num_rows
            from_row = 0
            while from_row < final_row:
                to_row = (from_row + 1) % num_rows
                if self.cucumbers[from_row][col] == "v" and self.cucumbers[to_row][col] == ".":
                    self.cucumbers[to_row][col] = "v"
                    self.cucumbers[from_row][col] = "."
                    changed = True
                    if from_row == 0:
                        final_row -= 1
                    from_row += 1
                from_row += 1
        if changed:
            self.num_steps += 1
        return changed

    @classmethod
    def load(cls, path: Path) -> "Trench":
        with open(path, "r") as f:
            return cls([list(line.strip()) for line in f])

    def __str__(self):
        return "\n".join(("".join(row) for row in self.cucumbers))


class SeaCucumber(Challenge):
    day = 25

    @Challenge.register_part(0)
    def steps(self):
        trench = Trench.load(self.input_path)
        print(str(trench))
        while trench.step():
            print(trench.num_steps)
            print(str(trench))
        self.output.write(f"{trench.num_steps + 1}\n")
