from pathlib import Path
from typing import Optional, TextIO

from . import Challenge


class SonarSweep(Challenge):
    day = 1

    def run(self, input_path: Path, output: TextIO, part: int = 0):
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
