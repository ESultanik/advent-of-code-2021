from typing import Iterable, Optional, Sequence, Set, Tuple

from . import Challenge


class InfiniteImage:
    def __init__(
            self,
            light_pixels: Iterable[Tuple[int, int]],
            min_x: Optional[int] = None,
            max_x: Optional[int] = None,
            min_y: Optional[int] = None,
            max_y: Optional[int] = None,
            outer_pixels_are_dark: bool = True
    ):
        self.light_pixels: Set[Tuple[int, int]] = set(light_pixels)
        if max_x is None:
            self.max_x: int = max(x for x, _ in self.light_pixels)
        else:
            self.max_x = max_x
        if min_x is None:
            self.min_x: int = min(x for x, _ in self.light_pixels)
        else:
            self.min_x = min_x
        if max_y is None:
            self.max_y: int = max(y for _, y in self.light_pixels)
        else:
            self.max_y = max_y
        if min_y is None:
            self.min_y: int = min(y for _, y in self.light_pixels)
        else:
            self.min_y = min_y
        self.outer_pixels_are_dark: bool = outer_pixels_are_dark

    def is_light(self, x: int, y: int) -> bool:
        if x < self.min_x or x > self.max_x or y < self.min_y or y > self.max_y:
            return not self.outer_pixels_are_dark
        return (x, y) in self.light_pixels

    def neighborhood(self, x: int, y: int) -> Tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool]:
        return tuple(self.is_light(x + xoffset, y + yoffset) for yoffset in range(-1, 2) for xoffset in range(-1, 2))

    def __str__(self):
        return "\n".join((
            "".join((
                [".", "#"][self.is_light(x, y)]
                for x in range(self.min_x, self.max_x + 1)
            ))
            for y in range(self.min_y, self.max_y + 1)
        ))


class EnhancementAlgorithm:
    def __init__(self, mapping: Sequence[bool]):
        self.mapping: Sequence[bool] = mapping

    def enhance(self, image: InfiniteImage) -> InfiniteImage:
        light_pixels = []
        new_min_x = image.min_x - 2
        new_max_x = image.max_x + 2
        new_min_y = image.min_y - 2
        new_max_y = image.max_y + 2
        for x in range(new_min_x, new_max_x + 1):
            for y in range(new_min_y, new_max_y + 1):
                value = 0
                for n in image.neighborhood(x, y):
                    value <<= 1
                    if n:
                        value |= 0b1
                if self.mapping[value]:
                    light_pixels.append((x, y))
        if image.outer_pixels_are_dark:
            new_outer_pixels_are_dark = not self.mapping[0]
        else:
            new_outer_pixels_are_dark = not self.mapping[0b111111111]
        return InfiniteImage(
            light_pixels=light_pixels,
            min_x=new_min_x,
            max_x=new_max_x,
            min_y=new_min_y,
            max_y=new_max_y,
            outer_pixels_are_dark=new_outer_pixels_are_dark
        )


class TrenchMap(Challenge):
    day = 20

    def load(self) -> Tuple[InfiniteImage, EnhancementAlgorithm]:
        with open(self.input_path, "r") as f:
            algorithm = None
            light_pixels = []
            row = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if algorithm is None:
                    algorithm = EnhancementAlgorithm([c == "#" for c in line])
                else:
                    for col, c in enumerate(line):
                        if c == "#":
                            light_pixels.append((col, row))
                    row += 1
        return InfiniteImage(light_pixels), algorithm

    @Challenge.register_part(0)
    def pixel_count(self):
        image, algorithm = self.load()
        print(str(image))
        image = algorithm.enhance(image)
        print()
        print(str(image))
        image = algorithm.enhance(image)
        print()
        print(str(image))
        assert image.outer_pixels_are_dark
        self.output.write(f"{len(image.light_pixels)}\n")

    @Challenge.register_part(1)
    def lots_of_pixels(self):
        image, algorithm = self.load()
        for i in range(50):
            print(f"Enhancement {i + 1}...")
            image = algorithm.enhance(image)
        assert image.outer_pixels_are_dark
        self.output.write(f"{len(image.light_pixels)}\n")
