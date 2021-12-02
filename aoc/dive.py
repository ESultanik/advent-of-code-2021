from enum import auto, Enum
from typing import Iterator, Tuple

from . import Challenge


class Command(Enum):
    FORWARD = auto()
    DOWN = auto()
    UP = auto()

    @staticmethod
    def parse(command: str) -> "Command":
        command_upper = command.upper()
        if not hasattr(Command, command_upper):
            raise ValueError(f"No such command {command}")
        return getattr(Command, command_upper)


class Position:
    def __init__(self, depth: int = 0, position: int = 0):
        self.depth: int = depth
        self.position: int = position

    def apply(self, command: Command, distance: int) -> "Position":
        command_name = command.name.lower()
        if not hasattr(self, command_name):
            raise TypeError(f"{self.__class__.__name__} has no method `{command_name}` for command {command}")
        return getattr(self, command_name)(distance)

    def forward(self, distance: int) -> "Position":
        return Position(depth=self.depth, position=self.position + distance)

    def down(self, distance: int) -> "Position":
        return Position(depth=self.depth + distance, position=self.position)

    def up(self, distance: int) -> "Position":
        return Position(depth=max(self.depth - distance, 0), position=self.position)


class Dive(Challenge):
    day = 2

    def read_input(self) -> Iterator[Tuple[Command, int]]:
        with open(self.input_path, "r") as f:
            for line in f:
                command_str, distance_str, *_ = line.split(" ")
                yield Command.parse(command_str), int(distance_str)

    @Challenge.register_part(0)
    def final_position(self):
        position = Position()
        for command, distance in self.read_input():
            position = position.apply(command, distance)
        self.output.write(f"{position.depth * position.position}\n")
