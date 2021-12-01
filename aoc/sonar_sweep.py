from pathlib import Path
from typing import List, TextIO

from . import Challenge


class SonarSweep(Challenge):
    day = 1

    @staticmethod
    def run_part0(input_path: Path, output: TextIO):
        prev_depth: Optional[int] = None
        larger_times = 0
        with open(input_path, "rb") as f:
            for line in f:
                depth = int(line.decode("utf-8"))
                if prev_depth is None:
                    prev_depth = depth
                else:
                    if depth > prev_depth:
                        larger_times += 1
                    prev_depth = depth
        output.write(f"{larger_times}\n")

    @staticmethod
    def run_part1(input_path: Path, output: TextIO):
        window: List[int] = []
        larger_times = 0
        with open(input_path, "rb") as f:
            for line in f:
                depth = int(line.decode("utf-8"))
                last_window = window
                window = window[-2:] + [depth]
                if len(last_window) >= 3:
                    if sum(window) > sum(last_window):
                        larger_times += 1
        output.write(f"{larger_times}\n")

    def run(self, input_path: Path, output: TextIO, part: int = 0):
        getattr(SonarSweep, f"run_part{part}")(input_path, output)
