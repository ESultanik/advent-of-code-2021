from abc import ABC, abstractmethod
from enum import Enum
import itertools
import json
from typing import Iterator, List, Optional, Sequence, Tuple, TypeVar, Union

from . import Challenge


class Side(Enum):
    ROOT = -1
    LEFT = 0
    RIGHT = 1


N = TypeVar("N")


class Number:
    def __init__(self, parent: Optional["Pair"] = None, side: Side = Side.ROOT):
        self.parent: Optional[Pair] = parent
        self.side: Side = side

    @abstractmethod
    def magnitude(self) -> int:
        raise NotImplementedError()

    def left_values(self) -> Iterator["RegularNumber"]:
        if self.parent is None:
            return
        if self.side == Side.RIGHT:
            yield from (n for n, _ in reversed(list(self.parent.left)) if isinstance(n, RegularNumber))
        yield from self.parent.left_values()

    def right_values(self) -> Iterator["RegularNumber"]:
        if self.parent is None:
            return
        if self.side == Side.LEFT:
            yield from (n for n, _ in self.parent.right if isinstance(n, RegularNumber))
        yield from self.parent.right_values()

    def __iter__(self) -> Tuple["Number", Sequence["Number"]]:
        stack = [(self, ())]
        while stack:
            number, ancestors = stack.pop()
            yield number, ancestors
            if isinstance(number, Pair):
                stack.append((number.right, ancestors + (number,)))
                stack.append((number.left, ancestors + (number,)))

    @abstractmethod
    def clone(self: N) -> N:
        raise NotImplementedError()


class RegularNumber(Number):
    def __init__(
            self,
            value: int,
            parent: Optional["Pair"] = None,
            side: Side = Side.ROOT
    ):
        super().__init__(parent=parent, side=side)
        self.value: int = value

    def magnitude(self) -> int:
        return self.value

    def clone(self) -> "RegularNumber":
        return RegularNumber(value=self.value, parent=self.parent, side=self.side)

    def __str__(self):
        return str(self.value)


class Pair(Number):
    def __init__(
            self,
            left: Number,
            right: Number,
            parent: Optional["Pair"] = None,
            side: Side = Side.ROOT
    ):
        super().__init__(parent=parent, side=side)
        self.left: Number = left
        self.right: Number = right
        left.parent = self
        right.parent = self
        left.side = Side.LEFT
        right.side = Side.RIGHT

    def magnitude(self) -> int:
        return 3 * self.left.magnitude() + 2 * self.right.magnitude()

    def clone(self) -> "Pair":
        l = self.left.clone()
        l.parent = self
        r = self.right.clone()
        r.parent = self
        return Pair(l, r, parent=self.parent, side=self.side)

    def __radd__(self, other) -> "Pair":
        if isinstance(other, int):
            if other != 0:
                raise ValueError("Can only add zero to a Pair")
            return self
        else:
            raise TypeError(f"Cannot add {other!r} to {self!r}")

    def __add__(self, other: "Number") -> "Pair":
        # print(f"{self!s} + {other!s}")
        result = Pair(self.clone(), other.clone())
        while True:
            exploded = False
            for number, ancestors in result:
                assert len(ancestors) < 5
                if isinstance(number, Pair) and len(ancestors) == 4:
                    # print(f"Explode {number!s}")
                    assert isinstance(number.left, RegularNumber)
                    assert isinstance(number.right, RegularNumber)
                    # the left value is added to the first regular number to the left of the exploding pair (if any)
                    for left in number.left_values():
                        left.value += number.left.value
                        break
                    for right in number.right_values():
                        right.value += number.right.value
                        break
                    if number.side == Side.LEFT:
                        number.parent.left = RegularNumber(0, parent=number.parent, side=Side.LEFT)
                    else:
                        number.parent.right = RegularNumber(0, parent=number.parent, side=Side.RIGHT)
                    # print(f"After explode: {ancestors[0]!s}")
                    break
            else:
                for number, ancestors in result:
                    if isinstance(number, RegularNumber) and number.value >= 10:
                        # print(f"Split {number!s}")
                        assert len(ancestors) > 0 and number.side != Side.ROOT
                        left_value = number.value // 2
                        new_pair = Pair(RegularNumber(left_value), RegularNumber(number.value - left_value),
                                        parent=number.parent, side=number.side)
                        if number.side == Side.LEFT:
                            number.parent.left = new_pair
                        else:
                            number.parent.right = new_pair
                        # print(f"After split: {ancestors[0]!s}")
                        break
                else:
                    # we neither split nor exploded
                    break
        return result

    @staticmethod
    def construct(number_list: Sequence[Union[int, Sequence]]) -> "Pair":
        assert len(number_list) == 2
        left, right = number_list
        if isinstance(left, int):
            left = RegularNumber(left)
        else:
            left = Pair.construct(left)
        if isinstance(right, int):
            right = RegularNumber(right)
        else:
            right = Pair.construct(right)
        return Pair(left, right)

    def __str__(self):
        return f"[{self.left!s}, {self.right!s}]"


class Snailfish(Challenge):
    day = 18

    def load(self) -> Iterator[Pair]:
        with open(self.input_path, "r") as f:
            for line in f:
                yield Pair.construct(json.loads(line))

    @Challenge.register_part(0)
    def magnitude(self):
        numbers = list(self.load())
        total = sum(numbers)
        print(total)
        self.output.write(f"{total.magnitude()}")

    @Challenge.register_part(1)
    def largest(self):
        numbers = list(self.load())
        biggest: Optional[int] = None
        for n1, n2 in itertools.combinations(numbers, 2):
            total = max((n1 + n2).magnitude(), (n2 + n1).magnitude())
            if biggest is None or biggest < total:
                biggest = total
        self.output.write(f"{biggest}")
