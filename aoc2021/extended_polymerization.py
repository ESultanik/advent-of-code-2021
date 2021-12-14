from typing import Dict, List, Tuple

from . import Challenge


class ExtendedPolymerization(Challenge):
    day = 14

    def load(self) -> Tuple[str, str, List[str], Dict[str, str]]:
        with open(self.input_path, "r") as f:
            first_line = f.readline().strip()
            first_char = first_line[0]
            last_char = first_line[-1]
            template = ["".join(c) for c in zip(first_line, first_line[1:])]
            rules = {}
            for line in f:
                line = line.strip()
                if not line:
                    continue
                arrow_pos = line.find("->")
                if arrow_pos <= 0:
                    continue
                rules[line[:arrow_pos].strip()] = line[arrow_pos + 2:].strip()
        return first_char, last_char, template, rules

    @Challenge.register_part(0)
    def commonality(self):
        print(self.load())
