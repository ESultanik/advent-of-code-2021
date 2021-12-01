from abc import ABCMeta
from functools import partial
from importlib import import_module
from inspect import isabstract
from pathlib import Path
from pkgutil import iter_modules
from typing import Callable, Dict, Iterator, Optional, TextIO, Type


class ChallengeMeta(ABCMeta):
    parts: Dict[int, Callable[["Challenge"], Optional[int]]] = {}

    def __len__(self):
        return self.parts

    def __getitem__(self, part: int) -> Callable[["Challenge"], Optional[int]]:
        return self.parts[part]

    def __iter__(self) -> Iterator[int]:
        yield from sorted(self.parts.keys())


class Challenge(metaclass=ChallengeMeta):
    name: str
    day: int

    @staticmethod
    def register_part(part: Optional[int] = 0, challenge: Optional[Type["Challenge"]] = None):
        def wrapper(func: Callable[["Challenge"], Optional[int]]):
            if challenge is None:
                # we are registering a member function of a challenge
                setattr(func, "_challenge_part", part)
            else:
                if part in challenge.parts:
                    raise TypeError(f"Challenge {challenge.name} for day {challenge.day} already has part {part} "
                                    f"registered as function {challenge.parts[part]}")
                challenge.parts[part] = func
            return func
        return wrapper

    def __init__(self, input_path: Path, output: TextIO):
        self.input_path: Path = input_path
        self.output: TextIO = output

    def __init_subclass__(cls, **kwargs):
        if not isabstract(cls):
            if not hasattr(cls, "name") or cls.name is None:
                setattr(cls, "name", cls.__name__)
            if cls.name in CHALLENGES:
                raise TypeError(f"A challenge named {cls.name} already exists!")
            elif not hasattr(cls, "day") or cls.day is None:
                raise TypeError(f"Challenge class {cls.__name__} must set its `day` member variable")
            elif cls.day in DAYS:
                raise TypeError(f"A challenge named {DAYS[cls.day].name} already exists for day {cls.day}!")
            for func in cls.__dict__.values():
                if hasattr(func, "_challenge_part"):
                    part = func._challenge_part
                    if part in cls.parts:
                        raise TypeError(f"Challenge {cls.name} for day {cls.day} already has part {part} "
                                        f"registered as function {cls.parts[part]}")
                    cls.parts[part] = func
            if cls.parts:
                # the challenge has at least one part
                missing_parts = sorted(set(range(max(cls.parts.keys()) + 1)) - cls.parts.keys())
                if missing_parts:
                    raise TypeError(f"Challenge {cls.name} for day {cls.day} is missing these parts: {missing_parts!r}")
                CHALLENGES[cls.name] = cls
                DAYS[cls.day] = cls

    @property
    def num_parts(self) -> int:
        return len(self.__class__.parts)

    def run_part(self, part: int) -> int:
        retval = self.__class__.parts[part](self)
        if retval is None:
            retval = 0
        return retval


CHALLENGES: Dict[str, Type[Challenge]] = {}
DAYS: Dict[int, Type[Challenge]] = {}

# Automatically load all modules in the `it_depends` package,
# so all DependencyClassifiers will auto-register themselves:
package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([str(package_dir)]):  # type: ignore
    # import the module and iterate through its attributes
    if module_name != "__main__":
        module = import_module(f"{__name__}.{module_name}")
