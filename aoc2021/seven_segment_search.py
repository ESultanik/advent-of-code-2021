from collections import Counter
from enum import auto, Enum
import itertools
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set

from . import Challenge


class Segment(Enum):
    TOP = auto()
    RIGHT_TOP = auto()
    LEFT_TOP = auto()
    MIDDLE = auto()
    BOTTOM = auto()
    RIGHT_BOTTOM = auto()
    LEFT_BOTTOM = auto()

    def __str__(self):
        if self == Segment.TOP:
            return "↑"
        elif self == Segment.BOTTOM:
            return "↓"
        elif self == Segment.MIDDLE:
            return "-"
        elif self == Segment.RIGHT_TOP:
            return "↗"
        elif self == Segment.RIGHT_BOTTOM:
            return "↘"
        elif self == Segment.LEFT_TOP:
            return "↖"
        elif self == Segment.LEFT_BOTTOM:
            return "↙"
        else:
            return super().__str__()


class Digit(Enum):
    ZERO = (0, {s for s in Segment if s != Segment.MIDDLE})
    ONE = (1, {Segment.RIGHT_TOP, Segment.RIGHT_BOTTOM})
    TWO = (2, {Segment.TOP, Segment.RIGHT_TOP, Segment.MIDDLE, Segment.LEFT_BOTTOM, Segment.BOTTOM})
    THREE = (3, {Segment.TOP, Segment.RIGHT_TOP, Segment.MIDDLE, Segment.RIGHT_BOTTOM, Segment.BOTTOM})
    FOUR = (4, {Segment.LEFT_TOP, Segment.MIDDLE, Segment.RIGHT_TOP, Segment.RIGHT_BOTTOM})
    FIVE = (5, {Segment.TOP, Segment.LEFT_TOP, Segment.MIDDLE, Segment.RIGHT_BOTTOM, Segment.BOTTOM})
    SIX = (6, {
        Segment.TOP, Segment.LEFT_TOP, Segment.MIDDLE, Segment.RIGHT_BOTTOM, Segment.BOTTOM, Segment.LEFT_BOTTOM
    })
    SEVEN = (7, {Segment.TOP, Segment.RIGHT_TOP, Segment.RIGHT_BOTTOM})
    EIGHT = (8, set(Segment))
    NINE = (9, {s for s in Segment if s != Segment.LEFT_BOTTOM})

    def __init__(self, digit: int, segments: Iterable[Segment]):
        self.digit: int = digit
        self.segments: FrozenSet[Segment] = frozenset(segments)

    def __str__(self):
        return str(self.digit)


class CodedDigit:
    def __init__(self, coded_segments: Iterable["CodedSegment"]):
        self.coded_segments: FrozenSet[CodedSegment] = frozenset(coded_segments)
        self._possibilities: FrozenSet[Digit] = frozenset(
            {d for d in Digit if len(self.coded_segments) == len(d.segments)}
        )
        # print(f"Initializing coded digit {self!s}")
        for segment in self.coded_segments:
            segment.add_used_in(self)

    def __eq__(self, other):
        return isinstance(other, CodedDigit) and self.coded_segments == other.coded_segments

    def __hash__(self):
        return hash(self.coded_segments)

    @property
    def possibilities(self) -> FrozenSet[Digit]:
        return self._possibilities

    @possibilities.setter
    def possibilities(self, new_possibilities: Iterable[Digit]):
        new_possibilities = frozenset(new_possibilities) & self._possibilities
        if new_possibilities != self._possibilities:
            # print(f"{self!s} removing {{{','.join(map(str, self._possibilities - new_possibilities))}}}")
            assert new_possibilities
            self._possibilities = new_possibilities
            self.propagate()

    def propagate(self):
        # perform constraint propagation
        for segment in self.coded_segments:
            segment.possibilities = segment.possibilities & self.possible_segments

    @property
    def possible_segments(self) -> Set[Segment]:
        return set().union(*(p.segments for p in self.possibilities)) & \
               set().union(*(s.possibilities for s in self.coded_segments))

    def __str__(self):
        return f"{''.join(str(s) for s in self.coded_segments)}={{{','.join(map(str, self.possibilities))}}}"


class CodedSegment:
    def __init__(self, code: str):
        if len(code) != 1:
            raise ValueError("The code must be a single character")
        self.code: str = code
        self._possibilities: FrozenSet[Segment] = frozenset(Segment)
        self._used_in: Set[CodedDigit] = set()
        self._other_segments: Set[CodedSegment] = set()

    @property
    def used_in(self) -> Iterable[CodedDigit]:
        return self._used_in

    def add_used_in(self, digit: CodedDigit):
        self._used_in.add(digit)
        self._other_segments |= digit.coded_segments - {self}
        self.possibilities = self.possibilities & digit.possible_segments
        self.propagate()

    @property
    def possibilities(self) -> FrozenSet[Segment]:
        return self._possibilities

    @possibilities.setter
    def possibilities(self, new_possibilities: Iterable[Segment]):
        new_possibilities = frozenset(new_possibilities) & self._possibilities
        if new_possibilities != self._possibilities:
            # print(f"{self!s} removing {{{','.join(map(str, self._possibilities - new_possibilities))}}}")
            assert new_possibilities
            self._possibilities = new_possibilities
            self.propagate()

    def propagate(self):
        # perform constraint propagation
        if len(self.possibilities) == 1:
            for other in self._other_segments:
                other.possibilities = other.possibilities - self.possibilities
        for digit in self.used_in:
            digit.possibilities = (d for d in digit.possibilities if d.segments & self._possibilities)
            # print(f"Updated: {digit!s}")
        # do we have only one of the possibilities that satisfies a digit?
        for digit in self.used_in:
            required_segments = set(Segment).intersection(*(p.segments for p in digit.possibilities))
            if not required_segments:
                # the possibilities of this digit do not have any overlapping segments
                continue
            for i in range(1, len(digit.coded_segments)):
                # if there is a group of i coded segments that each have the same i possibilities
                # that are all required for the digit's possibilities,
                # then remove those possibilities from all other coded segments not in the group
                for group in itertools.combinations(digit.coded_segments, i):
                    if all(
                            len(cd.possibilities) == i and required_segments.issuperset(cd.possibilities)
                            for cd in group
                    ):
                        all_match = True
                        last: Optional[CodedSegment] = None
                        for cd in group:
                            if last is not None and last.possibilities != cd.possibilities:
                                all_match = False
                                break
                            last = cd
                        if all_match:
                            # print(f"{', '.join(map(str, group))} collectively satisfy required segments in {digit!s}")
                            for other_segment in digit.coded_segments:
                                if other_segment not in group:
                                    other_segment.possibilities = other_segment.possibilities - group[0].possibilities
            if len(self.possibilities) > 1:
                # if we are the only option within a digit that can satisfy a required segment,
                # then that must be our only possibility!
                our_required_segments = self.possibilities & required_segments
                our_unique_required_segments = our_required_segments - set().union(*(
                    s.possibilities for s in digit.coded_segments if s != self
                ))
                if len(our_unique_required_segments) == 1:
                    # print(f"{self!s} is the only possibility in {digit!s} that satisfies "
                    #       f"{', '.join(map(str, our_required_segments))}")
                    self.possibilities = our_required_segments

    def __eq__(self, other):
        return isinstance(other, CodedSegment) and other.code == self.code

    def __hash__(self):
        return hash(self.code)

    def __str__(self):
        return f"{self.code}{{{','.join(map(str, self.possibilities))}}}"


class SevenSegmentSearch(Challenge):
    day = 8

    @Challenge.register_part(0)
    def digits(self):
        digits = Counter()
        with open(self.input_path, "r") as f:
            for line in f:
                _, raw_digits, *_ = line.split("|")
                for number in raw_digits.strip().split():
                    digits[len(number)] += 1
        self.output.write(f"{digits[2] + digits[3] + digits[4] + digits[7]}\n")

    @staticmethod
    def decode_entry(signals: Sequence[str], digits: Sequence[str]) -> int:
        # print(f"Decoding {' '.join(signals)} | {' '.join(digits)}")
        coded_segments: Dict[str, CodedSegment] = {
            c: CodedSegment(c)
            for c in ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        }
        signal_digits: List[CodedDigit] = [
            CodedDigit((coded_segments[c] for c in signal))
            for signal in signals
        ]
        coded_digits: List[CodedDigit] = [
            CodedDigit((coded_segments[c] for c in digit)) for digit in digits
        ]
        changed = True
        while changed:
            changed = False
            for coded_digit in coded_digits + signal_digits:
                if len(coded_digit.possibilities) == 1:
                    for other_digit in coded_digits + signal_digits:
                        if other_digit != coded_digit:
                            if coded_digit.possibilities & other_digit.possibilities:
                                other_digit.possibilities = other_digit.possibilities - coded_digit.possibilities
                                changed = True
        assert all(len(d.possibilities) == 1 for d in coded_digits)
        return sum(
            next(iter(d.possibilities)).digit * 10**(len(coded_digits) - i - 1) for i, d in enumerate(coded_digits)
        )

    @Challenge.register_part(1)
    def decode(self):
        with open(self.input_path, "r") as f:
            total = sum(
                SevenSegmentSearch.decode_entry(*(part.strip().split() for part in line.split("|")))
                for line in f
            )
        self.output.write(f"{total}\n")
