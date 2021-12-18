from enum import Enum
import math
from sympy import Integer, Piecewise, S, solve as symsolve, solveset, sqrt as symsqrt, Sum, symbols
from sympy.functions.elementary.miscellaneous import Min
import re
from typing import Iterator, Optional, Tuple

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
    for x, y in simulate(v_x, v_y):
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
) -> int:
    if target_min_x == target_max_x == initial_x:
        raise ValueError(f"Answer is infinite!")

    best_y = None
    for v_x in range(4, 11):
        for v_y in range(-257, 1000):
            result, max_y = calculate_result(v_x, v_y, target_min_x, target_max_x, target_min_y, target_max_y,
                                             initial_x, initial_y)
            if result == Result.SUCCESS:
                if best_y is None or best_y < max_y:
                    best_y = max_y
    return best_y

    v_x, v_y, i, apex_y = symbols("v_x v_y i apex_y", integer=True)
    step = symbols("step", integer=True, positive=True)
    x = Sum(v_x - i, (i, 0, Min(step, v_x))).doit()
    y = Sum(v_y - i, (i, 0, step)).doit()
    apex_y = Sum(v_y - i, (i, 0, v_y)).doit()
    min_v_x = int((math.sqrt(8 * target_min_x + 1) - 1) / 2)
    max_v_x = int((math.sqrt(8 * target_max_x + 1) - 1) / 2 + 0.5)
    for s in range(min_v_x, max_v_x + 1):
        solution = symsolve([
            y <= Integer(target_max_y),
            y >= Integer(target_min_y),
            min_v_x <= step,
            step <= max_v_x,
            v_y < step
        ], v_y, domain=S.Integers).subs(step, s).simplify()
        print(solution)
    exit(0)
    print(x)
    print(y)
    print(solveset(And(
        Integer(target_min_x) <= x,
        x <= Integer(target_max_x),
        step >= Integer(0)
    ), v_x))
    exit(0)

    min_v_x = int((math.sqrt(8 * target_min_x + 1) + 1)/2)
    max_v_x = int((math.sqrt(8 * target_max_x + 1) + 1)/2 + 0.5)
    best_y: Optional[int] = None
    for v_x in range(min_v_x, max_v_x + 1):
        if best_y is not None:
            # choose a minimum v_y such that it at least beats our best:
            #     minimize v_y subject to: best_y < sum(i, i=0..v_y)
            # solution: best_y * (best_y - 1) // 2
            min_v_y: Optional[int] = max(int((math.sqrt(8 * best_y + 1) + 1)/2 + 0.5), v_x)
            v_y = min_v_y
        else:
            min_v_y = None
        # max_steps = v_x
        # y needs to be within the range of the target within max_steps.
        # the number of steps to reach the apex is v_y, and the height of the apex is
        #     apex_y = v_y * (v_y - 1) // 2
        # let steps(fall_distance) be the minimum number of steps required to fall from the apex to fall_distance.
        #     steps(fall_distance) = int((math.sqrt(8 * fall_distance + 1) + 1)/2 + 0.5)
        # The number of steps until y passes the target, steps_to_target, is v_y + steps(apex_y - target_min_y)
        #     steps_to_target == max_steps
        #     v_y + int((math.sqrt(8 * (v_y * (v_y - 1) // 2 - target_min_y) + 1) + 1)/2 + 0.5) == max_steps
        max_v_y = int((4 * v_x**2 - 8 * v_x + 8 * target_min_y + 3) / (8 * v_x - 12) + 0.5)
        pass

    for v_x in range(min_v_x, max_v_x + 1):
        # the maximum number of steps that can execute before the x value passes the right side of the target:
        #     minimize max_steps subject to: target_max_x < sum(i,i=0..max_steps), max_steps <= v_x
        max_steps = max(int((math.sqrt(8 * target_max_x + 1) + 1)/2 + 0.5), v_x)
        # y needs to be less than or equal to target_max_y within max_steps.
        # the number of steps to reach the apex is min_v_y, and the height of the apex is
        #     apex_y = v_y * (v_y - 1) // 2
        # so the number of steps until y passes the target is v_y + (apex_y - target_max_y)
        # but we know that there are at most max_steps, so:
        #     max_steps >= v_y + apex_y - target_min_y
        #     max_steps >= v_y + v_y * (v_y - 1) // 2 - target_min_y
        # so
        #     max_v_y <= (sqrt(8 * max_steps + 8 * target_min_y + 1) - 1) / 2
        if target_min_y > 0 or max_steps > -target_min_y:
            max_v_y: Optional[int] = int((math.sqrt(8 * max_steps + 8 * target_min_y + 1) - 1) / 2 + 0.5)
        else:
            # we are just falling
            # TODO:
            pass
        if best_y is not None:
            # choose a minimum v_y such that it at least beats our best:
            #     minimize v_y subject to: best_y < sum(i, i=0..v_y)
            # solution: best_y * (best_y - 1) // 2
            min_v_y: Optional[int] = max(int((math.sqrt(8 * best_y + 1) + 1)/2 + 0.5), v_x)
            v_y = min_v_y
        else:
            min_v_y = None
            v_y = 0
        while True:
            print_trajectory(v_x, v_y, target_min_x, target_max_x, target_min_y, target_max_y)
            print(v_x, v_y, min_v_y, max_v_y, best_y)
            assert max_v_y is None or min_v_y is None or min_v_y <= v_y <= max_v_y
            result, max_y = calculate_result(v_x, v_y, target_min_x, target_max_x, target_min_y, target_max_y,
                                             initial_x, initial_y)
            if result == Result.SUCCESS:
                if best_y is None or best_y < max_y:
                    best_y = max_y
                if max_v_y is not None:
                    if max_v_y == v_y:
                        # the result can't get any better
                        break
                    elif max_v_y == v_y + 1:
                        v_y = max_v_y
                    else:
                        v_y = v_y + (max_v_y - v_y) // 2
                    continue
            elif result == Result.TOO_SLOW_Y:
                min_v_y = v_y + 1
            elif result == Result.TOO_FAST_Y:
                max_v_y = v_y - 1
            else:
                raise ValueError(f"Unexpected result: {result}")
            if max_v_y is None:
                if v_y < 0:
                    before = v_y
                    v_y //= 2
                    if v_y == before:
                        v_y += 1
                elif v_y > 0:
                    v_y *= 2
                else:
                    v_y = 1
            elif min_v_y is None:
                if v_y >= 0:
                    v_y = -1
                else:
                    if v_y < 0:
                        before = v_y
                        v_y //= 2
                        if v_y == before:
                            v_y += 1
                    elif v_y > 0:
                        v_y *= 2
                    else:
                        v_y = 1
                    if max_v_y is not None:
                        v_y = min(v_y, max_v_y)
            elif min_v_y == max_v_y:
                if best_y is None:
                    raise ValueError(f"Converged to {min_v_y} without finding a result!")
                else:
                    break
            else:
                before = v_y
                v_y = min_v_y + (max_v_y - min_v_y) // 2
                if v_y == before:
                    if v_y < max_v_y:
                        v_y += 1
                    else:
                        v_y -= 1
    if best_y is None:
        raise ValueError("No result found!")
    return best_y


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
        self.output.write(f"{solve(min_x, max_x, min_y, max_y)}\n")
        # print_trajectory(7, 2, 20, 30, -10, -5)

    @Challenge.register_part(1)
    def distinct(self):
        min_x, max_x, min_y, max_y = self.load()
        valid = 0
        for v_x in range(5, 51):
           for v_y in range(-257, 10000):
                result, _ = calculate_result(v_x, v_y, min_x, max_x, min_y, max_y)
                if result == Result.SUCCESS:
                    valid += 1
        self.output.write(f"{valid}\n")
