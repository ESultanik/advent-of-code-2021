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
    parser.add_argument("--part", "-p", type=int, default=0, help="the part of the challenge to run (default=0)")
    parser.add_argument("--output", "-o", type=str, help="path to the output file, or '-' for STDOUT (the default)",
                        default="-")

    args = parser.parse_args()

    if hasattr(args, "challenge") and args.challenge is not None:
        challenge_type = CHALLENGES[args.challenge]
    else:
        challenge_type = DAYS[args.day]

    if 0 > args.part >= challenge_type.parts:
        raise ValueError(f"--part must be in the range [0,{challenge_type.parts})")

    if args.output == "-":
        output = sys.stdout
    else:
        output = open(args.output, "w")

    challenge = challenge_type(args.INPUT, output)

    try:
        retval = challenge[args.part]()
        if retval is None:
            return 0
        else:
            return retval
    finally:
        if output is not sys.stdout:
            output.close()


if __name__ == "__main__":
    exit(main())
