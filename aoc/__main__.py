import argparse
from pathlib import Path
import sys

from . import CHALLENGES, DAYS


def main() -> int:
    parser = argparse.ArgumentParser(description="Evan Sultanik's Advent of Code Solutions")

    parser.add_argument("INPUT", type=Path, help="path to the input file")
    challenge_group = parser.add_mutually_exclusive_group(required=True)
    challenge_group.add_argument("--challenge", "-c", choices=sorted(CHALLENGES.keys()))
    challenge_group.add_argument("--day", "-d", choices=sorted(DAYS.keys()), help="the day number")
    parser.add_argument("--output", "-o", type=str, help="path to the output file, or '-' for STDOUT (the default)",
                        default="-")

    args = parser.parse_args()

    if hasattr(args, "challenge") and args.challenge is not None:
        challenge_type = CHALLENGES[args.challenge]
    else:
        challenge_type = DAYS[args.day]

    challenge = challenge_type()

    if args.output == "-":
        output = sys.stdout
    else:
        output = open(args.output, "w")

    try:
        retval = challenge.run(args.INPUT, output)
        if retval is None:
            return 0
        else:
            return retval
    finally:
        if output is not sys.stdout:
            output.close()


if __name__ == "__main__":
    exit(main())
