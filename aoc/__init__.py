from abc import ABC, abstractmethod
from importlib import import_module
from inspect import isabstract
from pathlib import Path
from pkgutil import iter_modules
from typing import Dict, TextIO, Type


class Challenge(ABC):
    name: str
    day: int
    parts: int = 2

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
            CHALLENGES[cls.name] = cls
            DAYS[cls.day] = cls

    @abstractmethod
    def run(self, input_path: Path, output: TextIO, part: int = 0):
        raise NotImplementedError()


CHALLENGES: Dict[str, Type[Challenge]] = {}
DAYS: Dict[int, Type[Challenge]] = {}

# Automatically load all modules in the `it_depends` package,
# so all DependencyClassifiers will auto-register themselves:
package_dir = Path(__file__).resolve().parent
for (_, module_name, _) in iter_modules([str(package_dir)]):  # type: ignore
    # import the module and iterate through its attributes
    if module_name != "__main__":
        module = import_module(f"{__name__}.{module_name}")
