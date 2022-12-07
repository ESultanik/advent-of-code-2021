from enum import IntEnum
import re
from typing import Callable, Iterator, List, Optional, Tuple, TypeVar, Union

from tqdm import tqdm

from . import Challenge


INPUT_PATTERN = re.compile(r"^\s*(?P<OnOff>on|off)\s+"
                           r"x\s*=\s*(?P<x1>-?\d+)\s*..\s*(?P<x2>-?\d+)\s*,"
                           r"y\s*=\s*(?P<y1>-?\d+)\s*..\s*(?P<y2>-?\d+)\s*,"
                           r"z\s*=\s*(?P<z1>-?\d+)\s*..\s*(?P<z2>-?\d+)\s*$")


class OctPos(IntEnum):
    TopRightFront = 0
    TopRightBack = 1
    TopLeftFront = 2
    TopLeftBack = 3
    BottomRightFront = 4
    BottomRightBack = 5
    BottomLeftFront = 6
    BottomLeftBack = 7

    @staticmethod
    def pos(left: bool, bottom: bool, back: bool) -> "OctPos":
        p = 0
        if back:
            p = 1
        p <<= 1
        if left:
            p |= 1
        p <<= 1
        if bottom:
            p |= 1
        return OctPos(p)

    @property
    def is_back(self) -> bool:
        return bool(self.value & 0b1)

    @property
    def is_left(self) -> bool:
        return bool(self.value & 0b10)

    @property
    def is_bottom(self) -> bool:
        return bool(self.value & 0b100)

    @staticmethod
    def get(location: "Region", inside: "Region") -> Iterator["OctPos"]:
        if location.volume == 1:
            if inside.volume < 8:
                raise ValueError(f"Region {inside} is too small! Expected a volume of at least 8.")
            elif not location in inside:
                raise ValueError(f"Point {location} is not inside region {inside}")
            is_left = location.min_point.x <= inside.min_point.x + (inside.max_point.x - inside.min_point.x) // 2
            is_bottom = location.min_point.y <= inside.min_point.y + (inside.max_point.y - inside.min_point.y) // 2
            is_back = location.min_point.z <= inside.min_point.z + (inside.max_point.z - inside.min_point.z) // 2
            yield OctPos.pos(is_left, is_bottom, is_back)
            return
        raise NotImplementedError("TODO")


class Region:
    def __init__(self, min_point: "Point", max_point: "Point"):
        self.min_point: Point = min_point
        self.max_point: Point = max_point
        #self._volume: Optional[int] = None
        if min_point is not None and max_point is not None:
            self.volume: int = self.width * self.height * self.depth
        else:
            self.volume: int = 0

    def __hash__(self):
        if self.volume == 0:
            return 0
        return hash((self.min_point, self.max_point))

    def __eq__(self, other):
        return isinstance(other, Region) and (
                (self.min_point == other.min_point and self.max_point == other.max_point)
                or
                (self.volume == 0 and other.volume == 0)
        )

    @staticmethod
    def bounding(*regions: "Region") -> "Region":
        min_x = min(r.min_point.x for r in regions)
        min_y = min(r.min_point.y for r in regions)
        min_z = min(r.min_point.z for r in regions)
        max_x = max(r.max_point.x for r in regions)
        max_y = max(r.max_point.y for r in regions)
        max_z = max(r.max_point.z for r in regions)
        return Region(
            min_point=Point(x=min_x, y=min_y, z=min_z),
            max_point=Point(x=max_x, y=max_y, z=max_z)
        )

    def double(self) -> "Region":
        half = Point(x=max(self.width // 2, 1), y=max(self.height // 2, 1), z=max(self.depth // 2, 1))
        return Region(min_point=self.min_point - half, max_point=self.max_point + half)

    @property
    def width(self) -> int:
        return max(self.max_point.x - self.min_point.x + 1, 0)

    @property
    def height(self) -> int:
        return max(self.max_point.y - self.min_point.y + 1, 0)

    @property
    def depth(self) -> int:
        return max(self.max_point.z - self.min_point.z + 1, 0)

    # @property
    # def volume(self) -> int:
    #     if self._volume is None:
    #         self._volume = self.width * self.height * self.depth
    #     return self._volume

    def __bool__(self):
        return self.volume > 0

    def subregions(self) -> Iterator[Tuple[OctPos, "Region"]]:
        mid_x = self.min_point.x + (self.max_point.x - self.min_point.x) // 2
        mid_y = self.min_point.y + (self.max_point.y - self.min_point.y) // 2
        mid_z = self.min_point.z + (self.max_point.z - self.min_point.z) // 2
        x_possibilities = [(True, self.min_point.x, mid_x)]
        if mid_x < self.max_point.x:
            x_possibilities.append((False, mid_x + 1, self.max_point.x))
        y_possibilities = [(True, self.min_point.y, mid_y)]
        if mid_y < self.max_point.y:
            y_possibilities.append((False, mid_y + 1, self.max_point.y))
        z_possibilities = [(True, self.min_point.z, mid_z)]
        if mid_z < self.max_point.z:
            z_possibilities.append((False, mid_z + 1, self.max_point.z))
        for left, min_x, max_x in x_possibilities:
            for bottom, min_y, max_y in y_possibilities:
                for back, min_z, max_z in z_possibilities:
                    yield OctPos.pos(left, bottom, back), Region(
                        min_point=Point(x=min_x, y=min_y, z=min_z),
                        max_point=Point(x=max_x, y=max_y, z=max_z)
                    )

    def __contains__(self, item):
        """Returns whether this region fully contains the given region or point"""
        if isinstance(item, Point):
            return self.min_point.x <= item.x <= self.max_point.x and \
                   self.min_point.y <= item.y <= self.max_point.y and \
                   self.min_point.z <= item.z <= self.max_point.z
        elif isinstance(item, Region):
            return self.min_point.x <= item.min_point.x <= item.max_point.x <= self.max_point.x and \
                   self.min_point.y <= item.min_point.y <= item.max_point.y <= self.max_point.y and \
                   self.min_point.z <= item.min_point.z <= item.max_point.z <= self.max_point.z
        else:
            return False

    def intersects(self, region: "Region") -> bool:
        """Returns whether this region intersects with the other region"""
        return not (
            self.max_point.x < region.min_point.x  # our right face is to the left of their left face
            or
            region.max_point.x < self.min_point.x  # their right face is to the left of our left face
            or
            self.max_point.z < region.min_point.z  # our front face is behind their back face
            or
            region.max_point.z < self.min_point.z  # their front face is behind our back face
            or
            self.max_point.y < region.min_point.y  # our top face is under their bottom face
            or
            region.max_point.y < self.min_point.y  # their top face is under our back face
        )

    def intersect(self, region: "Region") -> "Region":
        return Region(
            min_point=Point(
                x=max(region.min_point.x, self.min_point.x),
                y=max(region.min_point.y, self.min_point.y),
                z=max(region.min_point.z, self.min_point.z)
            ),
            max_point=Point(
                x=min(region.max_point.x, self.max_point.x),
                y=min(region.max_point.y, self.max_point.y),
                z=min(region.max_point.z, self.max_point.z)
            )
        )

    __and__ = intersect

    def union(self, region: "Region") -> "Region":
        return Region(
            min_point=Point(
                x=min(region.min_point.x, self.min_point.x),
                y=min(region.min_point.y, self.min_point.y),
                z=min(region.min_point.z, self.min_point.z)
            ),
            max_point=Point(
                x=max(region.max_point.x, self.max_point.x),
                y=max(region.max_point.y, self.max_point.y),
                z=max(region.max_point.z, self.max_point.z)
            )
        )

    __or__ = union

    def __sub__(self, other: "Region") -> Iterator["Region"]:
        if self == other:
            return
        overlap = self & other
        if not overlap:
            return
        x_positions = (
            (self.min_point.x, overlap.min_point.x - 1),
            (overlap.min_point.x, overlap.max_point.x),
            (overlap.max_point.x + 1, self.max_point.x)
        )
        y_positions = (
            (self.min_point.y, overlap.min_point.y - 1),
            (overlap.min_point.y, overlap.max_point.y),
            (overlap.max_point.y + 1, self.max_point.y)
        )
        z_positions = (
            (self.min_point.z, overlap.min_point.z - 1),
            (overlap.min_point.z, overlap.max_point.z),
            (overlap.max_point.z + 1, self.max_point.z)
        )
        for min_x, max_x in x_positions:
            if min_x > max_x:
                continue
            for min_y, max_y in y_positions:
                if min_y > max_y:
                    continue
                for min_z, max_z in z_positions:
                    if min_z > max_z:
                        continue
                    region = Region(
                        min_point=Point(min_x, min_y, min_z),
                        max_point=Point(max_x, max_y, max_z)
                    )
                    if region and region != overlap:
                        assert not (region & overlap)
                        assert region in self
                        yield region

    def __repr__(self):
        return f"{self.__class__.__name__}(min_point={self.min_point!r}, max_point={self.max_point!r})"

    def __str__(self):
        return f"x={self.min_point.x}..{self.max_point.x}," \
               f"y={self.min_point.y}..{self.max_point.y}," \
               f"z={self.min_point.z}..{self.max_point.z}"


class Point(Region):
    def __init__(self, x: int, y: int, z: int):
        super().__init__(None, None)  # type: ignore
        self.x: int = x
        self.y: int = y
        self.z: int = z
        self.min_point = self
        self.max_point = self
        self.volume = 1

    @property
    def width(self) -> int:
        return 1

    @property
    def height(self) -> int:
        return 1

    @property
    def depth(self) -> int:
        return 1

    def __eq__(self, other):
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y and self.z == other.z
        elif isinstance(other, Region):
            return other == self
        else:
            return False

    def _arithmetic(
            self, other: Union[int, "Point", Tuple[int, int, int]], operator: Callable[[int, int], int]
    ) -> "Point":
        if isinstance(other, Point):
            return Point(
                x=operator(self.x, other.x),
                y=operator(self.y, other.y),
                z=operator(self.z, other.z)
            )
        elif isinstance(other, int):
            return self._arithmetic((other, other, other), operator)
        elif len(other) == 3:
            return Point(
                x=operator(self.x, other[0]),
                y=operator(self.y, other[1]),
                z=operator(self.z, other[2])
            )
        else:
            raise NotImplementedError()

    def __add__(self, other) -> "Point":
        return self._arithmetic(other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other) -> "Point":
        return self._arithmetic(other, lambda a, b: a - b)

    def __rsub__(self, other) -> "Point":
        return self._arithmetic(other, lambda a, b: b - a)

    def __mul__(self, other) -> "Point":
        return self._arithmetic(other, lambda a, b: a * b)

    __rmul__ = __mul__

    def __repr__(self):
        return f"{self.__class__.__name__}(x={self.x}, y={self.y}, z={self.z})"

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"


T = TypeVar("T")


class Octree:
    def __init__(self, region: Region, is_on: bool = False):
        self.region: Region = region
        self.children: List[Optional[Octree]] = [None] * 8
        self._on: bool = is_on

    def clone(self: T) -> T:
        cloned = self.__class__(region=self.region, is_on=self.is_on)
        cloned.children = list(self.children)
        return cloned

    @property
    def is_on(self) -> bool:
        return self._on

    @is_on.setter
    def is_on(self, on: bool):
        self.children = [None] * 8
        self._on = on

    def __getitem__(self, item: OctPos) -> Optional["Octree"]:
        return self.children[item.value]

    def __setitem__(self, key: OctPos, value: Optional["Octree"]):
        self.children[key.value] = value

    @property
    def volume(self) -> int:
        return sum(d.region.volume for d in self.dfs())

    def dfs(self) -> Iterator["Octree"]:
        stack: List[Octree] = [self]
        while stack:
            node = stack.pop()
            if node.is_on:
                yield node
            else:
                stack.extend((node for node in node.children if node is not None))

    def add(self, region: Region):
        if region not in self.region:
            raise ValueError(f"Region {region} is not fully contained within {self}!")
        work: List[Tuple[Octree, Region, List[Octree]]] = [(self, region, [])]
        with tqdm(desc=f"adding", total=region.volume, unit="regions", leave=False, delay=2.0) as t:
            while work:
                octree, region, ancestors = work.pop()
                if octree.is_on and region in octree.region:
                    # the region is already on!
                    t.update(octree.volume)
                    continue
                elif region == octree.region:
                    # the region exactly matches our region
                    octree.is_on = True
                    t.update(octree.volume)
                    continue
                # break the region up into quadrants and add them individually
                for pos, s in octree.region.subregions():
                    overlap = region & s
                    if overlap:
                        t.update(overlap.volume)
                        child = octree.children[pos]
                        if child is None or overlap == s or child.region in overlap:
                            child = Octree(overlap, is_on=True)
                            octree.children[pos] = child
                        elif overlap == child.region:
                            child.is_on = True
                        elif overlap not in child.region:
                            assert child.region != s
                            # the child's region does not fully encompass this quadrant
                            # so create a new intermediate node that is bigger
                            intermediate = Octree(s)
                            octree.children[pos] = intermediate
                            work.extend(
                                (intermediate, node.region, ancestors + [octree]) for node in child.dfs()
                                if node.region not in overlap
                            )
                            work.append((intermediate, overlap, ancestors + [octree]))
                        else:
                            work.append((child, overlap, ancestors + [octree]))
                for ancestor in reversed(ancestors + [octree]):
                    if ancestor.is_on:
                        continue
                    elif all(c is not None and c.is_on for c in ancestor.children) and \
                            sum(c.volume for c in ancestor.children) == ancestor.region.volume:
                        ancestor.is_on = True
                    else:
                        break

    def remove(self, region: "Region"):
        if region not in self.region:
            return
        work: List[Tuple[Octree, Region, List[Tuple[Octree, OctPos]]]] = [(self, region, [])]
        with tqdm(desc=f"removing", total=1, unit="regions", leave=False, delay=2.0) as t:
            while work:
                octree, region, ancestors = work.pop()
                t.update(1)
                if octree.region in region:
                    # this node is completely contained within the removed region
                    octree.is_on = False
                    assert ancestors[-1][0].children[ancestors[-1][1]] is octree
                else:
                    for i, child in enumerate(octree.children):
                        if child is None:
                            continue
                        overlap = child.region & region
                        if not overlap:
                            continue
                        elif child.is_on:
                            # this subregion was entirely enabled
                            # so disable it because it will no longer be entirely enabled
                            child.is_on = False
                            # we now need to add "on" regions for everything in this octree node
                            # that is _not_ in the overlap!
                            for still_on in child.region - overlap:
                                assert not (still_on & region)
                                child.add(still_on)
                        else:
                            work.append((child, overlap, ancestors + [(octree, OctPos(i))]))
                            t.total += 1
                if all(c is None for c in octree.children):
                    for (parent, child_pos) in reversed(ancestors):
                        parent.children[child_pos] = None
                        if any(c is not None for c in parent.children):
                            break

    def __contains__(self, region: Region):
        return region in self.region

    def __str__(self):
        num_children = f"[{sum(1 for c in self.children if c is not None)}]"
        return f"{[num_children, 'on'][self.is_on]} {self.region!s}"


class ReactorRobot(Challenge):
    day = 22

    def load(self) -> Iterator[Tuple[bool, Region]]:
        with open(self.input_path, "r") as f:
            for line in f:
                m = INPUT_PATTERN.match(line.strip())
                if m is None:
                    continue
                yield m.group("OnOff") == "on", Region(
                    min_point=Point(x=int(m.group("x1")), y=int(m.group("y1")), z=int(m.group("z1"))),
                    max_point=Point(x=int(m.group("x2")), y=int(m.group("y2")), z=int(m.group("z2")))
                )

    @Challenge.register_part(0)
    def cubes_on(self):
        init_area = Region(min_point=Point(-50, -50, -50), max_point=Point(50, 50, 50))
        tree = Octree(region=init_area)
        for is_on, region in self.load():
            if region in init_area:
                if is_on:
                    tree.add(region)
                else:
                    tree.remove(region)
        print(tree.volume)

    @Challenge.register_part(1)
    def full_reboot(self):
        regions = tuple(self.load())
        area = Region.bounding(*(region for _, region in regions))
        tree = Octree(region=area)
        with tqdm(desc="rebooting", total=len(regions), unit="steps", leave=False) as t:
            for i, (is_on, region) in enumerate(regions):
                t.write(f"{['REMOVE', 'ADD'][is_on]} {region} ({sum(1 for _ in tree.dfs())} nodes)")
                t.update(1)
                if is_on:
                    tree.add(region)
                else:
                    tree.remove(region)
        print(tree.volume)
