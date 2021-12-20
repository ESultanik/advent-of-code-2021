from enum import Enum
import math
import re
from typing import Dict, Iterator, List, Optional, Set, Tuple

from . import Challenge


class Result(Enum):
    SUCCESS = 0
    TOO_FAST_Y = 1
    TOO_SLOW_Y = 2


def simulate(v_x: int, v_y: int, initial_x: int = 0, initial_y: int = 0) -> Iterator[Tuple[int, int]]:
    x, y = initial_x, initial_y
    while True:
        x += v_x
        if v_x > 0:
            v_x -= 1
        elif v_x < 0:
            v_x += 1
        y += v_y
        v_y -= 1
        yield x, y


def print_trajectory(
        v_x: int,
        v_y: int,
        target_min_x: int,
        target_max_x: int,
        target_min_y: int,
        target_max_y: int,
        initial_x: int = 0,
        initial_y: int = 0
):
    positions: List[Tuple[int, int]] = []
    max_x = max(initial_x, target_max_x)
    max_y = max(initial_y, target_max_y)
    min_x = min(initial_x, target_min_x)
    min_y = min(initial_y, target_min_y)
    for x, y in simulate(v_x, v_y, initial_x, initial_y):
        if y < target_min_y or x > target_max_x:
            break
        positions.append((x, y))
        min_x = min(x, min_x)
        min_y = min(y, min_y)
        max_x = max(x, max_x)
        max_y = max(y, max_y)
        if target_min_x <= x <= target_max_x and target_min_y <= y <= target_max_y:
            break
    field = [["." for _ in range(max_x - min_x + 1)] for _ in range(max_y - min_y + 1)]
    field[initial_y - min_y][initial_x - min_x] = "S"
    for y in range(target_min_y, target_max_y + 1):
        for x in range(target_min_x, target_max_x + 1):
            field[y - min_y][x - min_x] = "T"
    for x, y in positions:
        field[y - min_y][x - min_x] = "#"
    print("\n".join(("".join(row) for row in reversed(field))))


def calculate_result(
        v_x: int,
        v_y: int,
        target_min_x: int,
        target_max_x: int,
        target_min_y: int,
        target_max_y: int,
        initial_x: int = 0,
        initial_y: int = 0
) -> Tuple[Result, int]:
    max_y: Optional[int] = None
    for x, y in simulate(v_x, v_y, initial_x=initial_x, initial_y=initial_y):
        if max_y is None or y > max_y:
            max_y = y
        if target_min_x <= x <= target_max_x and target_min_y <= y <= target_max_y:
            return Result.SUCCESS, max_y
        elif x > target_max_x or y < target_min_y:
            if y > target_max_y or x > target_max_x:
                return Result.TOO_FAST_Y, max_y
            elif y < target_min_y:
                return Result.TOO_SLOW_Y, max_y


def solve(
        target_min_x: int,
        target_max_x: int,
        target_min_y: int,
        target_max_y: int,
        initial_x: int = 0,
        initial_y: int = 0
) -> Iterator[Tuple[int, int, int]]:
    if target_min_x == target_max_x == initial_x:
        raise ValueError(f"Answer is infinite!")

    # Observations:
    #  1. if v_y is positive:
    #     1.1 the projectile will travel up for v_y steps before reaching the apex
    #     1.2 the projectile will eventually fall back to initial_y after 2 * v_y steps
    #     1.3 when the projectile reaches initial_y again, it will be traveling with velocity -v_y - 1
    #     1.4 the maximum value for v_y is initial_y - target_min_y + 1
    #  2. if v_y is non-positive, and for any v_x:
    #     2.1 the distance the projectile will travel after a subsequent `s` steps is:
    #             sum(v - i, i=0..s-1) = -s ( s - 2v - 1 ) / 2
    #         for the case of v_x, this is assuming s <= v_x
    #  3. the projectile will be in the target in...
    #     3.1 at least 1 step, if target_min_x <= v_x <= target_max_x
    #     3.2 at most:
    #             maximize s
    #             subject to
    #                 target_min_x <= -s ( s - 2v - 1 ) / 2 <= target_max_x
    #                 0 < s <= v
    #         = v_x, if 2 * target_min_x <= v_x**2 + v_x < 2 * target_max_x; or
    #           (sqrt((2 * v_x + 1)**2 - 8 * target_max_x) + v_x + 0.5) // 2, otherwise
    #  4. all integers in the range [sqrt(2 * target_min_x + 0.25), sqrt(2 * target_max_x + 0.25)] are valid values
    #     for v_x if step >= v_x
    assert target_min_y < 0
    max_steps = -target_min_y * 2
    post_stop_min = int(math.ceil(math.sqrt(2 * target_min_x + 0.25) - 0.5))
    post_stop_max = int(math.floor(math.sqrt(2 * target_max_x + 0.25) - 0.5))
    history: Dict[int, Set[int]] = {}
    for step in range(1, max_steps + 1):
        min_v_y = int(math.ceil(target_min_y / step + step / 2 - 0.5))
        max_v_y = int(math.floor(target_max_y / step + step / 2 - 0.5))
        for v_y in range(min_v_y, max_v_y + 1):
            min_v_x = int(math.ceil(max(target_min_x / step + step / 2 - 0.5, step)))
            max_v_x = int(math.floor(target_max_x / step + step / 2 - 0.5))
            possible_vx = set(range(min_v_x, max_v_x + 1)) | {
                v for v in range(post_stop_min, post_stop_max + 1) if v <= step
            }
            if v_y in history:
                possible_vx -= history[v_y]
                history[v_y] |= possible_vx
            else:
                history[v_y] = possible_vx
            for v_x in possible_vx:
                result, max_y = calculate_result(v_x, v_y, target_min_x, target_max_x, target_min_y, target_max_y,
                                                 initial_x, initial_y)
                assert result == Result.SUCCESS
                if result == Result.SUCCESS:
                    yield v_x, v_y, max_y


TARGET_PATTERN = re.compile(r"^\s*target\s+area:\s*x\s*=\s*(\d+)\s*..\s*(\d+),\s*y\s*=\s*(-?\d+)\s*..\s*(-?\d+)\s*$")


class TrickShot(Challenge):
    day = 17

    def load(self) -> Tuple[int, int, int, int]:
        with open(self.input_path, "r") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                m = TARGET_PATTERN.match(line)
                if not m:
                    raise ValueError(f"Invalid line {i + 1}: {line!r}")
                return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        raise ValueError(f"target area not found in {self.input_path}")

    @Challenge.register_part(0)
    def highest(self):
        min_x, max_x, min_y, max_y = self.load()
        self.output.write(f"{max(m for _, _, m in solve(min_x, max_x, min_y, max_y))}\n")
        # print_trajectory(7, 2, 20, 30, -10, -5)

    @Challenge.register_part(1)
    def distinct(self):
        min_x, max_x, min_y, max_y = self.load()
        valid = sum(1 for _ in solve(min_x, max_x, min_y, max_y))
        self.output.write(f"{valid}\n")
