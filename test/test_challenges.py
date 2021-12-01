from pathlib import Path
import sys
from unittest import TestCase

from aoc import DAYS

ROOT_DIR = Path(__file__).absolute().parent.parent
INPUTS_DIR = ROOT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "outputs"


class TestChallenges(TestCase):
    def test_all_challenges(self):
        for challenge in DAYS.values():
            default_input = INPUTS_DIR / f"day{challenge.day}.txt"
            if not default_input.exists():
                sys.stderr.write(f"Warning: No default input for challenge {challenge.name}; "
                                 f"add one at {default_input!s}")
                continue
            output_path = OUTPUTS_DIR / f"day{challenge.day}.txt"
            with open(output_path, "w") as f:
                retval = challenge().run(default_input, f)
                if retval is None:
                    retval = 0
            self.assertEqual(retval, 0)
