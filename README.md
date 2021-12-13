# Advent of Code 2021
These are [Evan Sultanik](https://www.sultanik.com)’s solutions to the
[2021 Advent of Code](https://adventofcode.com/2021/) challenges.

This year I tried to write as performant solutions as possible (to the extent that that _is_
possible in Python), all the while making the code as readable and self-documenting as possible.

## Running the Code

```commandline
$ https://github.com/ESultanik/advent-of-code-2021.git
$ cd advent-of-code-2021 
$ pip3 install -e .
$ aoc2021 --help
```

You can use the `aoc2021` program to run each challenge by name or day.

You can also run all of the solved challenges on Evan’s personally assigned inputs
by running
```commandline
$ pip3 install pytest
$ pytest .
```

## Using the Framework

This repo contains a custom framework for quickly implementing solutions to Advent of Code
challenges in Python.  To reuse it:

```python
from aoc2021 import Challenge

class YourChallenge(Challenge):
    day = 1337  # the day number for the challenge

    @Challenge.register_part(0)
    def first_part(self):
        with open(self.input_path, "r") as f:
            print(f"Input file contents: {f.read()}")
        self.output.write("The solution goes here")
```

This challenge will automatically be registered, become available from the
`aoc2021` CLI, and be run with the unit tests. The unit tests will automatically
run it against `inputs/day1337.txt` and save the output to `outputs/day1337part0.txt`

## License

Copyright ©2021, Evan Sultanik. This code is licensed and distributed under the [AGPLv3 license](LICENSE).
