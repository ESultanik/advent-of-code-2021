from pathlib import Path
import subprocess
import sys
from time import process_time
from typing import Optional, Type
from unittest import TestCase

from aoc2021 import Challenge, DAYS

ROOT_DIR = Path(__file__).absolute().parent.parent
INPUTS_DIR = ROOT_DIR / "inputs"
OUTPUTS_DIR = ROOT_DIR / "outputs"


class TestChallenges(TestCase):
    def run_challenge_test(self, challenge: Type[Challenge], part: int):
        default_input = INPUTS_DIR / f"day{challenge.day}part{part}.txt"
        if not default_input.exists():
            # see if we have a generic input for the entire day:
            default_input = INPUTS_DIR / f"day{challenge.day}.txt"
            if not default_input.exists():
                sys.stderr.write(f"Warning: No default input for challenge {challenge.name} part {part}; "
                                 f"add one at {default_input!s}")
                return
        output_path = OUTPUTS_DIR / f"day{challenge.day}part{part}.txt"
        expected_output: Optional[bytes] = None
        # is there an existing output?
        if output_path.exists():
            # is the output checked into `git` and unmodified?
            if subprocess.call(
                    ["git", "ls-files", "--error-unmatch", output_path.name], cwd=output_path.parent,
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
            ) == 0 and subprocess.call(
                ["git", "diff", "--exit-code", output_path.name], cwd=output_path.parent,
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
            ) == 0:
                # the output is checked in and unmodified, so test our result against that output
                with open(output_path, "rb") as f:
                    expected_output = f.read()
        with open(output_path, "w") as f:
            start_time = process_time()
            retval = challenge(default_input, f).run_part(part)
            end_time = process_time()
            sys.stderr.write(f"Challgenge {challenge.day} part {part} completed in {end_time - start_time} "
                             "seconds\n")
        self.assertEqual(retval, 0)
        if expected_output is not None:
            # test the output against what was expected:
            with open(output_path, "rb") as f:
                new_output = f.read()
            self.assertEqual(expected_output, new_output)


def _challenge_test_wrapper(challenge: Type[Challenge], part: int):
    def wrapper(self: TestChallenges):
        return self.run_challenge_test(challenge, part)
    return wrapper


def _add_all_challenges():
    """Adds each challenge as a separate test in `TestChallenges`"""
    for _, challenge_type in sorted(DAYS.items()):
        for part in challenge_type:
            sys.stderr.write(f"Making test_{challenge_type.name}_part{part}\n")
            setattr(TestChallenges, f"test_{challenge_type.name}_part{part}",
                    _challenge_test_wrapper(challenge_type, part))


_add_all_challenges()
