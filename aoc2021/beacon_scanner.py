from collections import Counter
from enum import Enum
import itertools
from typing import FrozenSet, Iterable, Iterator, List, Optional, Tuple, Union

from . import Challenge


class Point:
    def __init__(self, x: int, y: int, z: int):
        self.x: int = x
        self.y: int = y
        self.z: int = z

    def distance_to(self, point: "Point") -> int:
        return abs(self.x - point.x) + abs(self.y - point.y) + abs(self.z - point.z)

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __add__(self, addend: "Point") -> "Point":
        return Point(x=self.x + addend.x, y=self.y + addend.y, z=self.z + addend.z)

    def __sub__(self, subtrahend: "Point") -> "Point":
        return Point(x=self.x - subtrahend.x, y=self.y - subtrahend.y, z=self.z - subtrahend.z)

    def __str__(self):
        return f"{self.x},{self.y},{self.z}"


class Axis(Enum):
    X = 0
    Y = 1
    Z = 2


class Angle(Enum):
    ZERO = (0, 1, 0)
    NINETY = (90, 0, 1)
    ONE_EIGHTY = (180, -1, 0)
    TWO_SEVENTY = (270, 0, -1)

    def __init__(self, angle: int, cos: int, sin: int):
        self.angle: int = angle
        self.cos: int = cos
        self.sin: int = sin

    def negate(self) -> "Angle":
        if self == Angle.NINETY:
            return Angle.TWO_SEVENTY
        elif self == Angle.TWO_SEVENTY:
            return Angle.NINETY
        else:
            return self

    def __str__(self):
        return str(self.angle)


class FacingDirection(Enum):
    POS_X = (Axis.X, True)
    NEG_X = (Axis.X, False)
    POS_Y = (Axis.Y, True)
    NEG_Y = (Axis.Y, False)
    POS_Z = (Axis.Z, True)
    NEG_Z = (Axis.Z, False)

    def __init__(self, axis: Axis, is_positive: bool):
        self.axis: Axis = axis
        self.is_positive: bool = is_positive


class AffineTransform:
    _IDENTITY: "AffineTransform"

    def __init__(self, matrix: Tuple[Tuple[int, int, int],Tuple[int, int, int],Tuple[int, int, int]]):
        self.matrix: Tuple[Tuple[int, int, int],Tuple[int, int, int],Tuple[int, int, int]] = matrix

    def __str__(self):
        return str(self.matrix)

    def __eq__(self, other):
        return isinstance(other, AffineTransform) and other.matrix == self.matrix

    def __hash__(self):
        return hash(self.matrix)

    @property
    @classmethod
    def IDENTITY(cls) -> "AffineTransform":
        if not hasattr(cls, "_IDENTITY") or cls._IDENTITY is None:
            cls._IDENTITY = AffineTransform(
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1)
            )
        return cls._IDENTITY

    def __mul__(self, point_or_transform: Union["AffineTransform", Point]) -> Union[Point, "AffineTransform"]:
        if isinstance(point_or_transform, Point):
            point = point_or_transform
            return Point(
                x=self.matrix[0][0] * point.x + self.matrix[0][1] * point.y + self.matrix[0][2] * point.z,
                y=self.matrix[1][0] * point.x + self.matrix[1][1] * point.y + self.matrix[1][2] * point.z,
                z=self.matrix[2][0] * point.x + self.matrix[2][1] * point.y + self.matrix[2][2] * point.z,
            )
        elif isinstance(point_or_transform, AffineTransform):
            m1 = self.matrix
            m2 = point_or_transform.matrix
            return AffineTransform(
                matrix=(
                    (
                        m1[0][0] * m2[0][0] + m1[0][1] * m2[1][0] + m1[0][2] * m2[2][0],
                        m1[0][0] * m2[0][1] + m1[0][1] * m2[1][1] + m1[0][2] * m2[2][1],
                        m1[0][0] * m2[0][2] + m1[0][1] * m2[1][2] + m1[0][2] * m2[2][2],
                    ),
                    (
                        m1[1][0] * m2[1][0] + m1[1][1] * m2[1][0] + m1[1][2] * m2[2][0],
                        m1[1][0] * m2[1][1] + m1[1][1] * m2[1][1] + m1[1][2] * m2[2][1],
                        m1[1][0] * m2[1][2] + m1[1][1] * m2[1][2] + m1[1][2] * m2[2][2],
                    ),
                    (
                        m1[2][0] * m2[1][0] + m1[2][1] * m2[1][0] + m1[2][2] * m2[2][0],
                        m1[2][0] * m2[1][1] + m1[2][1] * m2[1][1] + m1[2][2] * m2[2][1],
                        m1[2][0] * m2[1][2] + m1[2][1] * m2[1][2] + m1[2][2] * m2[2][2],
                    ),
                )
            )
        else:
            raise ValueError(f"Cannot multiply {self!s} with {point_or_transform!r}")


class Rotation:
    _POSSIBLE_COMBINATIONS: FrozenSet[Tuple["Rotation", ...]]

    def __init__(self, angle: Angle, axis: Axis):
        self.angle: Angle = angle
        self.axis: Axis = axis

    def __eq__(self, other):
        return isinstance(other, Rotation) and self.matrix() == other.matrix()

    def __hash__(self):
        return hash(self.matrix().matrix)

    @classmethod
    def all(cls) -> Iterator["Rotation"]:
        for angle in Angle:
            for axis in Axis:
                yield Rotation(angle, axis)

    @classmethod
    def all_combinations(cls) -> FrozenSet[Tuple["Rotation", ...]]:
        if not hasattr(cls, "_POSSIBLE_COMBINATIONS") or cls._POSSIBLE_COMBINATIONS is None:
            existing_matrices = set()
            combinations = []
            for r1 in cls.all():
                r1mat = r1.matrix()
                for r2 in cls.all():
                    r2mat = r2.matrix()
                    if r1mat == r2mat:
                        continue
                    for r3 in cls.all():
                        r3mat = r3.matrix()
                        if r3mat == r1mat or r3mat == r2mat:
                            continue
                        matrix = r1mat * r2mat * r3mat
                        if matrix not in existing_matrices:
                            combinations.append((r1, r2, r3))
                            existing_matrices.add(matrix)
            # assert len(combinations) == 24
            cls._POSSIBLE_COMBINATIONS = frozenset(combinations)
        return cls._POSSIBLE_COMBINATIONS


    def matrix(self) -> AffineTransform:
        cos = self.angle.cos
        sin = self.angle.sin
        if self.axis == Axis.Y:
            return AffineTransform((
                (cos, 0, sin),
                (0, 1, 0),
                (-sin, 0, cos)
            ))
        elif self.axis == Axis.X:
            return AffineTransform((
                (1, 0, 0),
                (0, cos, -sin),
                (0, sin, cos)
            ))
        else:
            return AffineTransform((
                (cos, -sin, 0),
                (sin, cos, 0),
                (0, 0, 1)
            ))

    def __str__(self):
        return f"Rotate<{self.axis.name},{self.angle}°>"


class Transform:
    _IDENTITY: "Transform"

    def __init__(self, translation: Point, rotations: Iterable[Rotation] = (), parent: Optional["Transform"] = None):
        self.rotation: AffineTransform = None  # type: ignore
        for rotation in rotations:
            if self.rotation is None:
                self.rotation = rotation.matrix()
            else:
                self.rotation *= rotation.matrix()
        if self.rotation is None:
            self.rotation = AffineTransform.IDENTITY
        self.translation: Point = translation
        self.parent: Optional[Transform] = parent

    def apply(self, results: "ScanResults") -> "ScanResults":
        transform: Optional[Transform] = self
        while transform is not None:
            results = ScanResults((transform.rotation * p + transform.translation for p in results.points))
            transform = transform.parent
        return results

    def __add__(self, other: "Transform") -> "Transform":
        t = Transform(
            self.translation,
            parent=other
        )
        t.rotation = self.rotation
        return t

    @property
    @classmethod
    def IDENTITY(cls) -> "Transform":
        if not hasattr(cls, "IDENTITY") or cls._IDENTITY is None:
            cls._IDENTITY = Transform(translation=Point(0, 0, 0))
        return cls._IDENTITY


class ScanResults:
    def __init__(self, points: Iterable[Point]):
        self.points: List[Point] = list(points)

    def rotate(self, *rotations: Rotation) -> "ScanResults":
        if rotations:
            mat = rotations[0].matrix()
            for rotation in rotations[1:]:
                mat *= rotation.matrix()
        else:
            mat = AffineTransform.IDENTITY
        return ScanResults((mat * p for p in self.points))

    def translate(self, translation: Point) -> "ScanResults":
        return ScanResults((p + translation for p in self.points))

    def calculate_transform(self, results: "ScanResults", minimum_overlap: int = 12) -> Optional[Tuple[Transform, int]]:
        """
        Yields all transforms on this set of results such that there are at least minimum_overlap overlapping beacons in
        the provided results
        """
        for rotations in Rotation.all_combinations():
            rotated = self.rotate(*rotations)
            # find the translation that makes `rotated` maximally overlap with results
            possible_translations = Counter(
                target - point for point in rotated for target in results
            )
            for translation, match_frequency in possible_translations.items():
                if match_frequency < minimum_overlap:
                    continue
                matches = sum(1 for p in rotated if any(p + translation == t for t in results))
                assert matches > 0
                if matches >= minimum_overlap:
                    return Transform(translation=translation, rotations=rotations), matches
        return None

    def __iter__(self) -> Iterator[Point]:
        yield from self.points

    def __str__(self):
        return "\n".join(map(str, self.points))


class BeaconScanner(Challenge):
    day = 19

    def load(self) -> Iterator[ScanResults]:
        points: List[Point] = []
        with open(self.input_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("---"):
                    if points:
                        yield ScanResults(points)
                    points = []
                else:
                    points.append(Point(*map(int, line.split(","))))
        if points:
            yield ScanResults(points)

    def solve(self) -> Tuple[List[ScanResults], List[Point]]:
        scanners = list(self.load())
        transform_to_first_scanner: List[Optional[Transform]] = [None] * len(scanners)
        transformed: List[ScanResults] = list(scanners)
        transform_to_first_scanner[0] = Transform.IDENTITY
        absolute_scanner_positions = [None] * len(scanners)
        absolute_scanner_positions[0] = Point(0, 0, 0)
        while any(t is None for t in transform_to_first_scanner[1:]):
            for scanner_index, scanner, transform in \
                    zip(range(1, len(scanners)), scanners[1:], transform_to_first_scanner[1:]):
                if transform is not None:
                    continue
                for i, transform_to, transform_to_transform in \
                        zip(range(len(scanners)), scanners, transform_to_first_scanner):
                    if transform_to_transform is None:
                        continue
                    assert scanner_index != i
                    result = scanner.calculate_transform(transform_to)
                    if result is None:
                        # print(f"No direct translation from scanner {scanner_index} to scanner {i}")
                        pass
                    elif result is not None:
                        print(f"Scanner {scanner_index} has a mapping to scanner {i}")
                        transform, _ = result
                        if i == 0:
                            # this is a direct mapping to scanner zero
                            transform_to_first_scanner[scanner_index] = transform
                            assert transform_to_transform == Transform.IDENTITY
                        else:
                            # this is a mapping to another scanner that already has a mapping to scanner zero
                            transform_to_first_scanner[scanner_index] = transform + transform_to_transform
                        transformed[scanner_index] = transform_to_first_scanner[scanner_index].apply(scanner)
                        absolute_scanner_positions[scanner_index] = \
                            transform_to_first_scanner[scanner_index].apply(ScanResults((Point(0, 0, 0),))).points[0]
                        assert sum(
                            1 for p in transformed[scanner_index] if any(
                                t == p for tr in transformed[:scanner_index] + transformed[scanner_index+1:] for t in tr
                            )
                        ) >= 12
                        break
        return transformed, absolute_scanner_positions  # type: ignore

    @Challenge.register_part(0)
    def how_many(self):
        transformed, _ = self.solve()
        points = {
            p for s in transformed for p in s
        }
        self.output.write(f"{len(points)}\n")

    @Challenge.register_part(1)
    def max_distance(self):
        _, positions = self.solve()
        maximum = max(p1.distance_to(p2) for p1, p2 in itertools.combinations(positions, 2))
        self.output.write(f"{maximum}\n")
