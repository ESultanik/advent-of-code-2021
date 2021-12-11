from typing import Iterator, List, Set, Tuple

from . import Challenge


class Puzzle:
    def __init__(self, state: List[List[int]]):
        self.state = state

    def neighborhood(self, row: int, col: int) -> Iterator[int]:
        if 0 < row < len(self.state) - 1:
            row_range = range(row - 1, row + 2)
        elif 0 < row:
            row_range = range(row - 1, row + 1)
        elif row < len(self.state) - 1:
            row_range = range(row, row + 2)
        else:
            row_range = range(row, row + 1)
        if 0 < col < len(self.state[row]) - 1:
            col_range = range(col - 1, col + 2)
        elif 0 < col:
            col_range = range(col - 1, col + 1)
        elif col < len(self.state) - 1:
            col_range = range(col, col + 2)
        else:
            col_range = range(col, col + 1)
        yield from ((r, c) for r in row_range for c in col_range if r != row or c != col)

    def step(self) -> "Puzzle":
        next_state = Puzzle([
            [col + 1 for col in row]
            for row in self.state
        ])
        queue: List[Tuple[int, int]] = [
            (r, c) for r, row in enumerate(next_state.state) for c in range(len(row))
            if next_state.state[r][c] > 9
        ]
        flashed: Set[Tuple[int, int]] = set(queue)
        while queue:
            r, c = queue.pop()
            for nr, nc in next_state.neighborhood(r, c):
                next_state.state[nr][nc] += 1
                pos = (nr, nc)
                if pos not in flashed and next_state.state[nr][nc] > 9:
                    flashed.add(pos)
                    queue.append(pos)
        next_state.state = [
            [[col, 0][col > 9] for col in row]
            for row in next_state.state
        ]
        return next_state

    def flashes(self) -> int:
        return sum(sum(1 for energy in row if energy == 0) for row in self.state)

    def __str__(self):
        return "\n".join(("".join(map(str, row)) for row in self.state))


class DumboOctopus(Challenge):
    day = 11

    def load(self) -> Puzzle:
        with open(self.input_path, "r") as f:
            return Puzzle([[int(energy) for energy in line.strip()] for line in f])

    @Challenge.register_part(0)
    def flashes(self):
        puzzle = self.load()
        flashes = puzzle.flashes()
        for _ in range(100):
            puzzle = puzzle.step()
            flashes += puzzle.flashes()
        self.output.write(f"{flashes}\n")
