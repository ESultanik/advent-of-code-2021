from collections import Counter

from . import Challenge


class SevenSegmentSearch(Challenge):
    day = 8

    @Challenge.register_part(0)
    def digits(self):
        digits = Counter()
        with open(self.input_path, "r") as f:
            for line in f:
                _, raw_digits, *_ = line.split("|")
                for number in raw_digits.strip().split():
                    digits[len(number)] += 1
        self.output.write(f"{digits[2] + digits[3] + digits[4] + digits[7]}\n")
