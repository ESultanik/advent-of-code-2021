from typing import List, Optional, Tuple

from . import Challenge


DELIMITERS = (
    ("(", ")"),
    ("[", "]"),
    ("{", "}"),
    ("<", ">"),
)


def first_illegal_char(line: str) -> Optional[Tuple[int, str, str]]:
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
                    return i, expected, symbol
                # print(f"{'    ' * len(symbol_stack)}{closing}")
                break
    return None


class SyntaxScoring(Challenge):
    day = 10

    @Challenge.register_part(0)
    def errors(self):
        assert first_illegal_char("{([(<{}[<>[]}>{[]{[(<()>")[1:] == (']', '}')
        assert first_illegal_char("[[<[([]))<([[{}[[()]]]")[1:] == (']', ')')
        assert first_illegal_char("[{[{({}]{}}([{[{{{}}([]")[1:] == (')', ']')
        points = 0
        with open(self.input_path, "r") as f:
            for line in f:
                result = first_illegal_char(line)
                if result is None:
                    print(f"VALID   {line.strip()}")
                    continue
                offset, expected, illegal = result
                print(f"INVALID {line[:offset]}|EXPECTED {expected!r} BUT FOUND {illegal!r}|{line[offset+1:].strip()}")
                if illegal == ")":
                    points += 3
                elif illegal == "]":
                    points += 57
                elif illegal == "}":
                    points += 1197
                elif illegal == ">":
                    points += 25137
        self.output.write(f"{points}\n")
