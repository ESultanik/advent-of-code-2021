from pathlib import Path
import sys
from time import process_time
from unittest import TestCase

from aoc import DAYS

ROOT_DIR = Path(__file__).absolute().parent.parent
INPUTS_DIR = ROOT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "outputs"


class TestChallenges(TestCase):
    def test_all_challenges(self):
        for _, challenge_type in sorted(DAYS.items()):
            challenge = challenge_type
            for part in challenge_type:
                default_input = INPUTS_DIR / f"day{challenge.day}part{part}.txt"
                if not default_input.exists():
                    # see if we have a generic input for the entire day:
                    default_input = INPUTS_DIR / f"day{challenge.day}.txt"
                    if not default_input.exists():
                        sys.stderr.write(f"Warning: No default input for challenge {challenge.name} part {part}; "
                                         f"add one at {default_input!s}")
                        continue
                output_path = OUTPUTS_DIR / f"day{challenge.day}part{part}.txt"
                with open(output_path, "w") as f:
                    start_time = process_time()
                    retval = challenge(default_input, f).run_part(part)
                    end_time = process_time()
                    sys.stderr.write(f"Challgenge {challenge.day} part {part} completed in {end_time - start_time} "
                                     "seconds\n")
                self.assertEqual(retval, 0)
