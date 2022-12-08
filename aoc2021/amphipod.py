from collections import defaultdict
from enum import Enum
import heapq
from typing import Dict, Iterator, List, Optional, Set, Tuple

from . import Challenge


Energy = int

class Amphipod(Enum):
    AMBER = ("A", 1)
    BRONZE = ("B", 10)
    COPPER = ("C", 100)
    DESERT = ("D", 1000)

    def __init__(self, code: str, energy_per_step: Energy):
        self.code: str = code
        self.energy_per_step: Energy = energy_per_step


class Move:
    __slots__ = "from_position", "to_position"

    def __init__(self, from_position: int, to_position: int):
        self.from_position: int = from_position
        self.to_position: int = to_position


class InvalidMoveError(ValueError):
    pass


class State:
    __slots__ = "state",

    COLUMN: Tuple[int, ...] = (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
              2,    4,    6,    8,
              2,    4,    6,    8
    )

    def __init__(self, state: int):
        self.state: int = state

    def __len__(self):
        return 8

    def __getitem__(self, index: int) -> int:
        if index >= 8:
            raise IndexError(index)
        return (self.state >> (index * 5)) & 0b11111

    def __iter__(self) -> Iterator[Tuple[Amphipod, int]]:
        pods = (
            Amphipod.AMBER,
            Amphipod.AMBER,
            Amphipod.BRONZE,
            Amphipod.BRONZE,
            Amphipod.COPPER,
            Amphipod.COPPER,
            Amphipod.DESERT,
            Amphipod.DESERT
        )
        for i in range(len(self)):
            yield pods[i], self[i]

    def positions(self, amphipod: Amphipod) -> Tuple[int, int]:
        if amphipod == Amphipod.AMBER:
            return self[0], self[1]
        elif amphipod == Amphipod.BRONZE:
            return self[2], self[3]
        elif amphipod == Amphipod.COPPER:
            return self[4], self[5]
        elif amphipod == Amphipod.DESERT:
            return self[6], self[7]

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        elif self.state == other.state:
            return True
        # see if any of the pairs of amphipods are permuted
        return not any(
            frozenset(self.positions(amphipod)) != frozenset(other.positions(amphipod))
            for amphipod in (
                Amphipod.AMBER,
                Amphipod.BRONZE,
                Amphipod.COPPER,
                Amphipod.DESERT
            )
        )

    def __str__(self):
        s = "#" * 13
        positions = ["."] * 19
        for amphipod, space in self:
            positions[space] = amphipod.code
        s = f"{s}\n#{''.join(positions[:11])}#\n"
        s = f"{s}###{positions[11]}#{positions[12]}#{positions[13]}#{positions[14]}###\n"
        s = f"{s}  #{positions[15]}#{positions[16]}#{positions[17]}#{positions[18]}#\n  #########\n"
        return s

    def successors(self, goal: Optional["State"] = None) -> Iterator[Tuple[Move, "State", Energy]]:
        if goal is None:
            goal = GOAL_STATE
        positions: List[Optional[Amphipod]] = [None] * 19
        for amphipod, pos in self:
            positions[pos] = amphipod
        for amphipod_id in range(8):
            current_pos = self[amphipod_id]
            if current_pos == (amphipod_id // 2) + 15:
                # the Amphipod is already in the bottom of its goal room
                continue
            elif current_pos >= 15 and positions[current_pos - 4] is not None:
                # the Amphipod is blocked
                continue
            for move_to in (15, 16, 17, 18, 11, 12, 13, 14, 0, 10, 1, 9, 3, 5, 7):
                if move_to != current_pos:
                    if 11 <= move_to < 15 and positions[move_to + 4] is None:
                        # don't move to the upper part of a room if the bottom isn't occupied
                        continue
                    try:
                        move = Move(from_position=current_pos, to_position=move_to)
                        yield move, *self.apply(move, goal=goal)
                    except InvalidMoveError:
                        pass

    @staticmethod
    def is_room(location_id) -> bool:
        return location_id >= 11

    @staticmethod
    def path(from_position: int, to_position: int) -> Iterator[int]:
        """Yields all of the positions from from_position (non-inclusive) to to_position (inclusive)"""
        while from_position != to_position:
            if from_position >= 15:
                # bottom of a room
                pos = from_position - 4
            elif from_position >= 11:
                if to_position == from_position + 4:
                    # moving down in a room
                    pos = to_position
                else:
                    # moving out of a room into the hall
                    pos = State.COLUMN[from_position]
            elif from_position == 0:
                pos = 1
            elif from_position == 10:
                pos = 9
            else:
                from_col = State.COLUMN[from_position]
                to_col = State.COLUMN[to_position]
                if from_col == to_col:
                    # moving from a hallway into a room
                    assert to_position >= 11
                    if to_position < 15:
                        pos = to_position
                    else:
                        pos = to_position - 4
                elif from_col < to_col:
                    pos = from_position + 1
                else:
                    pos = from_position - 1
            yield pos
            from_position = pos

    def apply(self, move: Move, goal: Optional["State"] = None) -> Tuple["State", Energy]:
        if goal is None:
            goal = GOAL_STATE
        positions: List[Optional[Amphipod]] = [None] * 19
        for amphipod, space in self:
            positions[space] = amphipod
        amphipod = positions[move.from_position]
        if amphipod is None:
            raise InvalidMoveError(f"No Amphipod at space {move.from_position}")
        moving_to_room = State.is_room(location_id=move.to_position)
        if moving_to_room and move.to_position not in goal.positions(amphipod):
            raise InvalidMoveError(f"Cannot move {amphipod.code} to position {move.to_position} because it is not its "
                                   f"goal room")
        elif not State.is_room(location_id=move.from_position) and not moving_to_room:
            raise InvalidMoveError("A move from the hallway must be into a room")
        num_moves = 0
        for pos in State.path(from_position=move.from_position, to_position=move.to_position):
            num_moves += 1
            if positions[pos] is not None:
                raise InvalidMoveError(f"Position {pos} is occupied by {positions[pos].code}")
        positions[move.to_position] = amphipod
        positions[move.from_position] = None
        return State.create(*positions), amphipod.energy_per_step * num_moves

    @classmethod
    def create(cls, *spaces: Optional[Amphipod]) -> "State":
        if len(spaces) != 19:
            raise ValueError(f"Expected 19 spaces but got {len(spaces)}")
        non_empty = sum(1 for s in spaces if s is not None)
        if non_empty != 8:
            raise ValueError(f"Expected 8 non-empty spaces but got {non_empty}")
        amphipod_spaces: Dict[Amphipod, List[int]] = defaultdict(list)
        for i, space in enumerate(spaces):
            if space is None:
                continue
            existing_spaces = amphipod_spaces[space]
            if len(existing_spaces) >= 2:
                raise ValueError(f"Too many amphipods of type {space.code}")
            existing_spaces.append(i)
        if len(amphipod_spaces) != 4 or any(len(s) != 2 for s in amphipod_spaces.values()):
            raise ValueError("Did not get all 8 amphipods!")
        return cls(
            amphipod_spaces[Amphipod.AMBER][0] |
            (amphipod_spaces[Amphipod.AMBER][1] << 5) |
            (amphipod_spaces[Amphipod.BRONZE][0] << 10) |
            (amphipod_spaces[Amphipod.BRONZE][1] << 15) |
            (amphipod_spaces[Amphipod.COPPER][0] << 20) |
            (amphipod_spaces[Amphipod.COPPER][1] << 25) |
            (amphipod_spaces[Amphipod.DESERT][0] << 30) |
            (amphipod_spaces[Amphipod.DESERT][1] << 35)
        )

    @classmethod
    def parse(cls, state_str: str) -> "State":
        positions: List[Optional[Amphipod]] = []
        for c in state_str:
            if c == ".":
                positions.append(None)
            else:
                for a in Amphipod:
                    if a.code == c:
                        positions.append(a)
        return State.create(*positions)


GOAL_STATE = State.create(
    *([None] * 11 + [Amphipod.AMBER, Amphipod.BRONZE, Amphipod.COPPER, Amphipod.DESERT] * 2)  # type: ignore
)


class SearchNode:
    __slots__ = "state", "parent", "move", "total_energy", "heuristic"

    def __init__(self,
                 state: State,
                 parent: Optional["SearchNode"] = None,
                 move: Optional[Move] = None,
                 total_energy: int = 0
    ):
        self.state: State = state
        self.parent: Optional[SearchNode] = parent
        self.move: Optional[Move] = move
        self.total_energy: int = total_energy
        self.heuristic: int = 0
        positions: List[Optional[Amphipod]] = [None] * 19
        for amphoid, position in self.state:
            positions[position] = amphoid
        for amphoid, position in self.state:
            if amphoid == Amphipod.AMBER:
                if position in (11, 15):
                    continue
                goal_pos = 11
            elif amphoid == Amphipod.BRONZE:
                if position in (12, 16):
                    continue
                goal_pos = 12
            elif amphoid == Amphipod.COPPER:
                if position in (13, 17):
                    continue
                goal_pos = 13
            else:
                if position in (14, 18):
                    continue
                goal_pos = 14

            min_path_len = 0
            for pos in State.path(position, goal_pos):
                min_path_len += amphoid.energy_per_step
                blocking_amphipod = positions[pos]
                if blocking_amphipod is not None:
                    min_path_len += blocking_amphipod.energy_per_step
            self.heuristic += min_path_len

    def __eq__(self, other):
        return isinstance(other, SearchNode) and other.state == self.state and other.total_energy == self.total_energy

    def __hash__(self):
        return hash((self.state.state, self.total_energy))

    def __lt__(self, other):
        return isinstance(other, SearchNode) and \
            self.total_energy + self.heuristic < other.total_energy + other.heuristic

    def __str__(self):
        s = ""
        node = self
        while node:
            if node is self:
                down_arrow = ""
            else:
                down_arrow = "\n\n      |\n      V"
            s = f"{node.state!s}energy: {node.total_energy}{down_arrow}\n\n{s}"
            node = node.parent
        return s


def solve(start_state: State, goal_state: Optional[State] = None) -> SearchNode:
    if goal_state is None:
        goal_state = GOAL_STATE
    queue: List[SearchNode] = [SearchNode(start_state)]
    history: Set[SearchNode] = {queue[-1]}
    iterations = 0
    while queue:
        iterations += 1
        node = heapq.heappop(queue)
        if iterations % 1000 == 0:
            print(
                f"Iteration {iterations}\tQueue Size: {len(queue)}\tBest so far: {node.total_energy + node.heuristic}"
            )
            print(str(node.state))
        if node.state == goal_state:
            return node
        for move, state, energy in node.state.successors(goal=goal_state):
            new_node = SearchNode(
                state=state, parent=node, move=move, total_energy=node.total_energy + energy
            )
            if new_node not in history:
                history.add(new_node)
                heapq.heappush(queue, new_node)
    raise ValueError("No solution!")


class AmphipodChallenge(Challenge):
    day = 23

    @Challenge.register_part(0)
    def organize(self):
        with open(self.input_path, "r") as f:
            state = State.parse(f.read())
        print(str(state))
        solution = solve(state)
        print("==================[ SOLUTION ]==================")
        print(str(solution))
