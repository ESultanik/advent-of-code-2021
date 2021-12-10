import argparse
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

from . import CHALLENGES, DAYS


def main() -> int:
    parser = argparse.ArgumentParser(description="Evan Sultanik's Advent of Code Solutions")

    parser.add_argument("INPUT", type=Path, nargs="?", default=Path("-"),
                        help="path to the input file (default is STDIN)")
    challenge_group = parser.add_mutually_exclusive_group(required=True)
    challenge_group.add_argument("--challenge", "-c", choices=sorted(CHALLENGES.keys()))
    challenge_group.add_argument("--day", "-d", type=int, choices=sorted(DAYS.keys()), help="the day number")
    challenge_group.add_argument("--list", "-l", action="store_true", help="list all available challenges")
    parser.add_argument("--part", "-p", type=int, default=0, help="the part of the challenge to run (default=0)")
    parser.add_argument("--output", "-o", type=str, help="path to the output file, or '-' for STDOUT (the default)",
                        default="-")

    args = parser.parse_args()

    if hasattr(args, "list") and args.list:
        for day in sorted(DAYS):
            challenge = DAYS[day]
            print(f"Day {day}:\t{challenge.name} ({len(challenge.parts)} part{['', 's'][len(challenge.parts) != 1]})")
        return 0

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

    if str(args.INPUT) == "-":
        tmpfile = NamedTemporaryFile(delete=False)
        tmpfile.write(sys.stdin.read())
        tmpfile.close()
        input_path = tmpfile.name
    else:
        tmpfile = None
        input_path = args.INPUT

    try:
        challenge = challenge_type(input_path, output)

        try:
            retval = challenge.run_part(args.part)
            if retval is None:
                return 0
            else:
                return retval
        finally:
            if output is not sys.stdout:
                output.close()
    finally:
        if tmpfile is not None:
            Path(tmpfile.name).unlink()


if __name__ == "__main__":
    exit(main())
