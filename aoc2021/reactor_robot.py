from abc import ABC, abstractmethod
import re
from typing import Iterable, Iterator, List, Tuple

from . import Challenge


INPUT_PATTERN = re.compile(r"^\s*(?P<OnOff>on|off)\s+"
                           r"x\s*=\s*(?P<x1>-?\d+)\s*..\s*(?P<x2>-?\d+)\s*,"
                           r"y\s*=\s*(?P<y1>-?\d+)\s*..\s*(?P<y2>-?\d+)\s*,"
                           r"z\s*=\s*(?P<z1>-?\d+)\s*..\s*(?P<z2>-?\d+)\s*$")


class Region(ABC):
    @property
    @abstractmethod
    def volume(self) -> int:
        raise NotImplementedError()

    def __bool__(self):
        return self.volume > 0

    @abstractmethod
    def intersects(self, region: "Region") -> bool:
        raise NotImplementedError()

    @abstractmethod
    def __sub__(self, other) -> "Region":
        raise NotImplementedError()


class EmptyRegion(Region):
    @property
    def volume(self) -> int:
        return 0

    def intersects(self, region: "Region") -> bool:
        return False

    def __sub__(self, other):
        return self

    def __rsub__(self, other):
        return other


class Cube(Region):
    def __init__(self, min_x: int, max_x: int, min_y: int, max_y: int, min_z: int, max_z: int):
        if min_x > max_x:
            min_x, max_x = max_x, min_x
        if min_y > max_y:
            min_y, max_y = max_y, min_y
        if min_z > max_z:
            min_z, max_z = max_z, min_z
        self.min_x: int = min_x
        self.max_x: int = max_x
        self.min_y: int = min_y
        self.max_y: int = max_y
        self.min_z: int = min_z
        self.max_z: int = max_z

    @property
    def extrema(self) -> Tuple[int, int, int, int, int, int]:
        return self.min_x, self.max_x, self.min_y, self.max_y, self.min_z, self.max_z

    @property
    def width(self) -> int:
        return max(self.max_x - self.min_x, 0)

    @property
    def height(self) -> int:
        return max(self.max_y - self.min_y, 0)

    @property
    def depth(self) -> int:
        return max(self.max_z - self.min_z, 0)

    @property
    def volume(self) -> int:
        return self.width * self.height * self.depth

    def intersects(self, region: Region) -> bool:
        if not isinstance(region, Cube):
            return region.intersects(self)
        return not (
            self.max_x < region.min_x  # our right face is to the left of their left face
            or
            region.max_x < self.min_x  # their right face is to the left of our left face
            or
            self.max_z < region.min_z  # our front face is behind their back face
            or
            region.max_z < self.min_z  # their front face is behind our back face
            or
            self.max_y < region.min_y  # our top face is under their bottom face
            or
            region.max_y < self.min_y  # their top face is under our back face
        )

    def __sub__(self, other) -> Region:
        if not isinstance(other, Cube):
            raise NotImplementedError()
        if not other.intersects(self):
            # they don't intersect us
            return self
        # split ourself into 27 cubes, some of which may be of zero volume
        components: List[Cube] = []
        for min_x, max_x in ((self.min_x, other.min_x - 1), (other.max_x + 1, self.max_x)):
            for min_y, max_y in ((self.min_y, other.min_y - 1), (other.max_y + 1, self.max_y)):
                for min_z, max_z in ((self.min_z, other.min_z - 1), (other.max_z + 1, self.max_z)):
                    cube = Cube(min_x, max_x, min_y, max_y, min_z, max_z)
                    if cube:
                        components.append(cube)
        if len(components) == 1:
            return components[0]
        elif not components:
            return EmptyRegion()
        else:
            return CompoundRegion(components)

    def __repr__(self):
        return f"{self.__class__.__name__}(" \
               f"{self.min_x},{self.max_x}," \
               f"{self.min_y},{self.max_y}," \
               f"{self.min_z},{self.max_z})"


class CompoundRegion(Region):
    def __init__(self, sub_regions: Iterable[Region]):
        self.sub_regions = tuple(sub_regions)

    def intersects(self, region: Region) -> bool:
        if isinstance(region, Cube):
            return any(r.intersects(region) for r in self.sub_regions)
        elif isinstance(region, CompoundRegion):
            return any(r1.intersects(r2) for r1 in self.sub_regions for r2 in region.sub_regions)
        raise NotImplementedError()

    @property
    def volume(self) -> int:
        return sum(r.volume for r in self.sub_regions)

    def __sub__(self, other) -> "Region":
        components: List[Region] = []
        for s in self.sub_regions:
            result = s - other
            if isinstance(result, CompoundRegion):
                components.extend(result.sub_regions)
            elif result:
                components.append(result)
        return CompoundRegion(components)


class ReactorRobot(Challenge):
    day = 22

    def load(self) -> Iterator[Tuple[bool, Cube]]:
        with open(self.input_path, "r") as f:
            for line in f:
                m = INPUT_PATTERN.match(line.strip())
                if m is None:
                    continue
                yield m.group("OnOff") == "on", Cube(
                    int(m.group("x1")), int(m.group("x2")),
                    int(m.group("y1")), int(m.group("y2")),
                    int(m.group("z1")), int(m.group("z2"))
                )

    @Challenge.register_part(0)
    def cubes_on(self):
        grid = EmptyRegion()
        for is_on, region in self.load():
            if all(-50 <= e <= 50 for e in region.extrema):
                grid = grid - region
                if is_on:
                    grid = CompoundRegion((grid, region))
        print(grid.volume)
