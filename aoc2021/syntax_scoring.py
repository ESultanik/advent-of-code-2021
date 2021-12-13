from typing import List, Iterable, Tuple, Union

from . import Challenge


DELIMITERS = (
    ("(", ")"),
    ("[", "]"),
    ("{", "}"),
    ("<", ">"),
)


class Corruption:
    def __init__(self, offset: int, expected: str, illegal: str):
        self.offset: int = offset
        self.expected: str = expected
        self.illegal: str = illegal


class Completion:
    def __init__(self, completion: Iterable[str]):
        self.completion: Tuple[str, ...] = tuple(completion)


def first_illegal_char(line: str) -> Union[Corruption, Completion]:
    symbol_stack: List[str] = []
    for i, symbol in enumerate(line):
        for opening, closing in DELIMITERS:
            if symbol == opening:
                # print(f"{'    ' * len(symbol_stack)}{symbol}")
                symbol_stack.append(closing)
                break
            elif symbol == closing:
                if not symbol_stack:
                    expected = None
                else:
                    expected = symbol_stack.pop()
                if expected != symbol:
                    return Corruption(i, expected, symbol)
                # print(f"{'    ' * len(symbol_stack)}{closing}")
                break
    return Completion(reversed(symbol_stack))


class SyntaxScoring(Challenge):
    day = 10

    @Challenge.register_part(0)
    def errors(self):
        points = 0
        with open(self.input_path, "r") as f:
            for line in f:
                result = first_illegal_char(line)
                if not isinstance(result, Corruption):
                    print(f"VALID   {line.strip()}")
                    continue
                print(f"INVALID {line[:result.offset]}|EXPECTED {result.expected!r} BUT FOUND "
                      f"{result.illegal!r}|{line[result.offset+1:].strip()}")
                if result.illegal == ")":
                    points += 3
                elif result.illegal == "]":
                    points += 57
                elif result.illegal == "}":
                    points += 1197
                elif result.illegal == ">":
                    points += 25137
        self.output.write(f"{points}\n")

    @Challenge.register_part(1)
    def completion(self):
        scores = []
        with open(self.input_path, "r") as f:
            for line in f:
                result = first_illegal_char(line)
                if not isinstance(result, Completion):
                    continue
                score = 0
                for c in result.completion:
                    p = (")", "]", "}", ">").index(c) + 1
                    score = score * 5 + p
                scores.append(score)
        scores = sorted(scores)
        self.output.write(f"{scores[len(scores) // 2]}\n")
