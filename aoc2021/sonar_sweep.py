from typing import List, Optional

from . import Challenge


class SonarSweep(Challenge):
    day = 1

    @Challenge.register_part(0)
    def larger_times(self):
        prev_depth: Optional[int] = None
        larger_times = 0
        with open(self.input_path, "rb") as f:
            for line in f:
                depth = int(line.decode("utf-8"))
                if prev_depth is None:
                    prev_depth = depth
                else:
                    if depth > prev_depth:
                        larger_times += 1
                    prev_depth = depth
        self.output.write(f"{larger_times}\n")

    @Challenge.register_part(1)
    def larger_windows(self):
        window: List[int] = []
        larger_times = 0
        with open(self.input_path, "rb") as f:
            for line in f:
                depth = int(line.decode("utf-8"))
                last_window = window
                window = window[-2:] + [depth]
                if len(last_window) >= 3:
                    if sum(window) > sum(last_window):
                        larger_times += 1
        self.output.write(f"{larger_times}\n")
