from typing import Iterator, List, Set, Tuple

from . import Challenge


RawRow = Tuple[int, ...]
RawCol = RawRow
RawBoard = Tuple[RawRow, ...]


class Board:
    def __init__(self, rows: RawBoard):
        self.rows: RawBoard = rows

    def row(self, index: int) -> RawRow:
        return self.rows[index]

    def col(self, index: int) -> RawCol:
        return tuple(row[index] for row in self.rows)

    def is_winner(self, numbers: Set[int]) -> bool:
        return any(all(v in numbers for v in row) for row in self.rows) or \
               any(all(v in numbers for v in col) for col in map(self.col, range(len(self.rows))))

    def __iter__(self) -> Iterator[int]:
        for row in self.rows:
            yield from row


class GiantSquid(Challenge):
    day = 4

    def parse_boards(self) -> Tuple[Tuple[int, ...], Tuple[Board, ...]]:
        with open(self.input_path, "r") as f:
            numbers = tuple(int(n) for n in f.readline().split(","))
            rows: List[RawRow] = []
            boards: List[Board] = []
            for line in f:
                row = line.strip().split()
                if len(row) == 5:
                    rows.append(tuple(map(int, row)))
                    if len(rows) == 5:
                        boards.append(Board(tuple(rows)))
                        rows = []
        return numbers, tuple(boards)

    @Challenge.register_part(0)
    def bingo(self):
        numbers, boards = self.parse_boards()

        history: Set[int] = set()

        for number in numbers:
            history.add(number)

            for board in boards:
                if board.is_winner(history):
                    unused = set(board) - history
                    score = sum(unused)
                    self.output.write(f"{score * number}\n")
                    return
