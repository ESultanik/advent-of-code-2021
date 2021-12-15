import heapq
from typing import Iterable, Iterator, List, Optional, Tuple

from . import Challenge


class SearchNode:
    def __init__(self, cavern: "Cavern", row: int = 0, col: int = 0, parent: Optional["SearchNode"] = None):
        self.row: int = row
        self.col: int = col
        self.cavern: Cavern = cavern
        self.parent: Optional[SearchNode] = parent
        if parent is None:
            assert row == 0 and col == 0
            self.path_cost: int = 0  # The starting position has no risk
        else:
            self.path_cost = parent.path_cost + self.cavern[row][col]
        min_remaining_moves = (self.cavern.width - (self.col + 1)) + (self.cavern.height - (self.row + 1))
        self.heuristic: int = min_remaining_moves
        self.f_cost: int = self.path_cost + self.heuristic

    @property
    def is_goal(self) -> bool:
        return self.row + 1 == self.cavern.height and self.col + 1 == self.cavern.width

    def path(self) -> List["SearchNode"]:
        n = self
        p: List[SearchNode] = []
        while n is not None:
            p.append(n)
            n = n.parent
        return list(reversed(p))

    def successors(self) -> Iterator["SearchNode"]:
        if self.is_goal:
            return
        if self.row > 0:
            yield SearchNode(cavern=self.cavern, row=self.row-1, col=self.col, parent=self)
        if self.row < self.cavern.height - 1:
            yield SearchNode(cavern=self.cavern, row=self.row+1, col=self.col, parent=self)
        if self.col > 0:
            yield SearchNode(cavern=self.cavern, row=self.row, col=self.col-1, parent=self)
        if self.col < self.cavern.width - 1:
            yield SearchNode(cavern=self.cavern, row=self.row, col=self.col+1, parent=self)

    def __hash__(self):
        return hash((self.row, self.col, self.path_cost))

    def __eq__(self, other):
        return isinstance(other, SearchNode) and other.row == self.row and other.col == self.col and \
               other.path_cost == self.path_cost

    def __lt__(self, other):
        if not isinstance(other, SearchNode):
            raise ValueError("Search nodes can only be compared to other search nodes")
        our_f = self.f_cost
        other_f = other.f_cost
        return our_f < other_f or (our_f == other_f and self.path_cost < other.path_cost)

    def __str__(self):
        path = ",".join(f"{node.row, node.col}" for node in self.path())
        return f"path_cost={self.path_cost}\theuristic={self.heuristic}\t{path}"

    def path_str(self) -> str:
        p = self.path()
        max_row = max(n.row for n in p)
        max_col = max(n.col for n in p)
        return "\n".join((
            "".join(
                [f" {col} ", f"[{col}]"][any(n.row == y and n.col == x for n in p)]
                for x, col in enumerate(row[:max_col + 2])
            )
            for y, row in enumerate(self.cavern.risks[:max_row + 2])
        ))


class Cavern:
    def __init__(self, risks: Iterable[Iterable[int]]):
        self.risks: List[List[int]] = [list(row) for row in risks]
        self.height: int = len(self.risks)
        self.width: int = max(len(row) for row in self.risks)

    def __getitem__(self, row: int) -> List[int]:
        return self.risks[row]

    def shortest_path(self, to_row: int, to_col: int) -> SearchNode:
        queue = [SearchNode(cavern=self)]
        first_heuristic = self.width + self.height
        best_heuristic = first_heuristic
        best_f_costs: Dict[Tuple[int, int], int] = {(0, 0): queue[0].f_cost}
        while queue:
            node = heapq.heappop(queue)
            h = node.heuristic
            if h < best_heuristic:
                # print(f"{(first_heuristic - h)/first_heuristic*100.0 + 0.5:05}%")
                best_heuristic = h
            # print(str(node))
            if node.is_goal:
                return node
            # print(node.path_str())
            # print(str(node))
            # print()
            for s in node.successors():
                pos = (s.row, s.col)
                if pos not in best_f_costs or best_f_costs[pos] > s.f_cost:
                    best_f_costs[pos] = s.f_cost
                    heapq.heappush(queue, s)
        raise ValueError(f"There is no path from (0, 0) to ({to_row}, {to_col})")

    def expand(self, original_width: int, original_height: int) -> "Cavern":
        upper_right: List[List[int]] = [
            [[c+1,1][c >= 9] for c in row[-original_width:]] for row in self.risks
        ]
        lower_left: List[List[int]] = [
            [[c+1,1][c >= 9] for c in row] for row in self.risks[-original_height:]
        ]
        lower_right: List[List[int]] = [
            [[c+1,1][c >= 9] for c in row] for row in upper_right[-original_height:]
        ]
        expanded: List[List[int]] = [
            self.risks[i] + upper_right[i]
            for i in range(self.height)
        ] + [
            lower_left[i] + lower_right[i]
            for i in range(original_height)
        ]
        return Cavern(expanded)

    def __str__(self):
        return "\n".join(("".join(map(str, row)) for row in self.risks))


class Chiton(Challenge):
    day = 15

    def load(self) -> Cavern:
        with open(self.input_path, "r") as f:
            return Cavern(
                (map(int, line.strip()) for line in f)
            )

    @Challenge.register_part(0)
    def lowest_risk(self):
        cavern = self.load()
        # print(str(cavern))
        node = cavern.shortest_path(to_row=cavern.height - 1, to_col=cavern.width - 1)
        self.output.write(f"{node.path_cost}\n")

    @Challenge.register_part(1)
    def larger_cavern(self):
        cavern = self.load()
        w, h = cavern.width, cavern.height
        for _ in range(4):
            cavern = cavern.expand(w, h)
        node = cavern.shortest_path(to_row=cavern.height - 1, to_col=cavern.width - 1)
        self.output.write(f"{node.path_cost}\n")
