from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import heapq
from typing import Dict, Iterator, List, Optional, Sequence, Set, Tuple

from . import Challenge


Energy = int


class Location(Enum):
    HALLWAY = 0
    ROOM1 = 2
    ROOM2 = 4
    ROOM3 = 6
    ROOM4 = 8

    @property
    def meets_hallway_at_index(self) -> int:
        return self.value


class Amphipod(Enum):
    AMBER = ("A", 1, Location.ROOM1)
    BRONZE = ("B", 10, Location.ROOM2)
    COPPER = ("C", 100, Location.ROOM3)
    DESERT = ("D", 1000, Location.ROOM4)

    def __init__(self, code: str, energy_per_step: Energy, goal_location: Location):
        self.code: str = code
        self.energy_per_step: Energy = energy_per_step
        self.goal_location: Location = goal_location


@dataclass(frozen=True)
class Position:
    location: Location
    index: int


@dataclass(frozen=True)
class Move:
    from_position: Position
    to_position: Position

    @property
    def path(self) -> Iterator[Position]:
        """Yields all of the positions from from_position (non-inclusive) to to_position (inclusive)"""
        pos = self.from_position
        while pos != self.to_position:
            if pos.location == self.to_position.location:
                if self.to_position.index > pos.index:
                    pos = Position(pos.location, pos.index + 1)
                else:
                    pos = Position(pos.location, pos.index - 1)
            elif pos.location == Location.HALLWAY:
                target_index = self.to_position.location.meets_hallway_at_index
                if pos.index == target_index:
                    # enter the room
                    pos = Position(self.to_position.location, 0)
                elif pos.index < target_index:
                    pos = Position(Location.HALLWAY, pos.index + 1)
                else:
                    pos = Position(Location.HALLWAY, pos.index - 1)
            elif pos.index == 0:
                # we need to enter the hallway
                pos = Position(Location.HALLWAY, pos.location.meets_hallway_at_index)
            else:
                # we are in the wrong room and need to make for the hallway
                pos = Position(pos.location, pos.index - 1)
            yield pos


class InvalidMoveError(ValueError):
    pass


class State:
    __slots__ = "locations", "_hash"

    def __init__(
            self,
            locations: Dict[Location, Sequence[Optional[Amphipod]]]
    ):
        self.locations: Dict[Location, Sequence[Optional[Amphipod]]] = locations
        self._hash: int = -1

    def __hash__(self):
        if self._hash < 0:
            self._hash = 0
            for loc, spots in self.locations.items():
                v = 0
                for s in spots:
                    v <<= 3
                    if s == Amphipod.AMBER:
                        v |= 1
                    elif s == Amphipod.BRONZE:
                        v |= 2
                    elif s == Amphipod.COPPER:
                        v |= 3
                    elif s == Amphipod.DESERT:
                        v |= 4
                self._hash |= v << (loc.value * 3)
        return self._hash

    def __getitem__(self, position: Position) -> Optional[Amphipod]:
        return self.locations[position.location][position.index]

    def __iter__(self) -> Iterator[Tuple[Amphipod, Position]]:
        for location, seq in self.locations.items():
            yield from (
                (a, Position(location=location, index=i)) for i, a in enumerate(seq) if a is not None
            )

    def positions(self, amphipod: Amphipod) -> Iterator[Position]:
        for a, pos in self:
            if a == amphipod:
                yield pos

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.locations == other.locations

    def __str__(self):
        s = ["#"] * 13
        s.append("\n#")

        def code_for(a: Optional[Amphipod]) -> str:
            if a is None:
                return "."
            else:
                return a.code

        s.extend(map(code_for, self.locations[Location.HALLWAY]))
        s.append("#\n")
        for i, (r1, r2, r3, r4) in enumerate(zip(
                self.locations[Location.ROOM1],
                self.locations[Location.ROOM2],
                self.locations[Location.ROOM3],
                self.locations[Location.ROOM4]
        )):
            if i == 0:
                s.append("###")
            else:
                s.append("  #")
            s.append(f"{code_for(r1)}#{code_for(r2)}#{code_for(r3)}#{code_for(r4)}#")
            if i == 0:
                s.append("##")
            s.append("\n")
        s.append("  #########\n")
        return "".join(s)

    def successors(self) -> Iterator[Tuple[Move, "State", Energy]]:
        open_positions = sorted([
            Position(location=location, index=i)
            for location, spots in self.locations.items()
            for i, spot in enumerate(spots)
            if spot is None and not (location == Location.HALLWAY and i in (2, 4, 6, 8))
            # don't move to the entry spot in the hallway
        ], key=lambda p: p.index, reverse=True)
        for location, spots in self.locations.items():
            if location == Location.HALLWAY:
                for i, spot in enumerate(spots):
                    if spot is None:
                        continue
                    room = self.locations[spot.goal_location]
                    if room[0] is None and all(s is None or s.goal_location == spot.goal_location for s in room[1:]):
                        # all of the spots in the goal room are occupied by other Amphipods of the same type
                        deepest_index = 0
                        while deepest_index < len(room) - 1 and room[deepest_index+1] is None:
                            deepest_index += 1
                        move = Move(
                            from_position=Position(location=location, index=i),
                            to_position=Position(location=spot.goal_location, index=deepest_index)
                        )
                        try:
                            yield move, *self.apply(move)
                        except InvalidMoveError:
                            pass
                        continue
            else:
                for i, spot in enumerate(spots):
                    if spot is None:
                        continue
                    elif spot.goal_location == location:
                        # we are in the correct room
                        if all(s is None or s.goal_location == location for s in spots[i+1:]):
                            # all of the spots in the room below us are occupied by other Amphoid's of the same type
                            if i < len(spots) - 1 and spots[i+1] is None:
                                # we can move down to make more room
                                move = Move(
                                    from_position=Position(location=location, index=i),
                                    to_position=Position(location=location, index=i+1)
                                )
                                yield move, *self.apply(move)
                            continue
                        # we are in the correct room, but there are incorrect Amphoids below us, so we'll have to
                        # move out of the way for them to leave
                        valid_locations = (Location.HALLWAY,)
                    else:
                        valid_locations = (Location.HALLWAY, spot.goal_location)
                    already_got_goal_position = False
                    for pos in open_positions:
                        if pos.location not in valid_locations or \
                                (already_got_goal_position and pos.location == spot.goal_location):
                            continue
                        move = Move(
                            from_position=Position(location, index=i),
                            to_position=pos
                        )
                        try:
                            yield move, *self.apply(move)
                            if pos.location == spot.goal_location:
                                already_got_goal_position = True
                        except InvalidMoveError:
                            pass

    def apply(self, move: Move) -> Tuple["State", Energy]:
        amphipod = self[move.from_position]
        if amphipod is None:
            raise InvalidMoveError(f"No Amphipod at space {move.from_position}")
        if move.to_position.location != Location.HALLWAY and move.to_position.location != amphipod.goal_location:
            raise InvalidMoveError(f"Cannot move {amphipod.code} to position {move.to_position} because it is not its "
                                   f"goal room")
        elif move.from_position.location == Location.HALLWAY and move.to_position.location == Location.HALLWAY:
            raise InvalidMoveError("A move from the hallway must be into a room")
        num_moves = 0
        for pos in move.path:
            num_moves += 1
            if self[pos] is not None:
                raise InvalidMoveError(f"Position {pos} is occupied by {self[pos].code}")
        new_locations = dict(self.locations)
        from_list = list(new_locations[move.from_position.location])
        from_list[move.from_position.index] = None
        new_locations[move.from_position.location] = from_list
        if move.to_position.location == move.from_position.location:
            to_list = from_list
        else:
            to_list = list(new_locations[move.to_position.location])
            new_locations[move.to_position.location] = to_list
        to_list[move.to_position.index] = amphipod
        return self.__class__(new_locations), num_moves * amphipod.energy_per_step

    @classmethod
    def create(cls, *spaces: Optional[Amphipod], expected_spaces: int = 19) -> "State":
        if len(spaces) != expected_spaces:
            raise ValueError(f"Expected {expected_spaces} spaces but got {len(spaces)}")
        non_empty = sum(1 for s in spaces if s is not None)
        if non_empty != expected_spaces - 11:
            raise ValueError(f"Expected {expected_spaces - 11} non-empty spaces but got {non_empty}")
        amphipod_spaces: Dict[Amphipod, List[int]] = defaultdict(list)
        room_height = (expected_spaces - 11) // 4
        for i, space in enumerate(spaces):
            if space is None:
                continue
            existing_spaces = amphipod_spaces[space]
            if len(existing_spaces) >= room_height:
                raise ValueError(f"Too many amphipods of type {space.code}")
            existing_spaces.append(i)
        if len(amphipod_spaces) != 4 or any(len(s) != room_height for s in amphipod_spaces.values()):
            raise ValueError(f"Did not get all {4 * room_height} amphipods!")
        locations: Dict[Location, List[Optional[Amphipod]]] = {
            Location.HALLWAY: [None] * 11,
            Location.ROOM1: [None] * room_height,
            Location.ROOM2: [None] * room_height,
            Location.ROOM3: [None] * room_height,
            Location.ROOM4: [None] * room_height
        }
        for amphipod, indexes in amphipod_spaces.items():
            for index in indexes:
                if index < 11:
                    locations[Location.HALLWAY][index] = amphipod
                else:
                    room_offset = (index - 11) % 4
                    if room_offset == 0:
                        locations[Location.ROOM1][(index - 11) // 4] = amphipod
                    elif room_offset == 1:
                        locations[Location.ROOM2][(index - 11) // 4] = amphipod
                    elif room_offset == 2:
                        locations[Location.ROOM3][(index - 11) // 4] = amphipod
                    elif room_offset == 3:
                        locations[Location.ROOM4][(index - 11) // 4] = amphipod
        return cls(locations)

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
        return cls.create(*positions)


class Part2State(State):
    @classmethod
    def create(cls, *spaces: Optional[Amphipod], expected_spaces: int = 27) -> "State":
        return super().create(*spaces, expected_spaces=expected_spaces)

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
                        if len(positions) == 15:
                            positions.extend((Amphipod.DESERT, Amphipod.COPPER, Amphipod.BRONZE, Amphipod.AMBER,
                                              Amphipod.DESERT, Amphipod.BRONZE, Amphipod.AMBER, Amphipod.COPPER))
        return cls.create(*positions)


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
        for amphipod, position in self.state:
            if position.location == amphipod.goal_location and all(
                spot is not None and spot.goal_location == position.location
                for spot in self.state.locations[position.location][position.index+1:]
            ):
                continue
            else:
                goal_pos = Position(amphipod.goal_location, 0)

            min_path_len = 0
            for pos in Move(from_position=position, to_position=goal_pos).path:
                min_path_len += amphipod.energy_per_step
                # blocking_amphipod = self.state[pos]
                # if blocking_amphipod is not None:
                #    min_path_len += blocking_amphipod.energy_per_step
            self.heuristic += min_path_len

    def is_goal(self) -> bool:
        return all(
            a.goal_location == p.location
            for a, p in self.state
        )

    def __eq__(self, other):
        return isinstance(other, SearchNode) and other.state == self.state and other.total_energy == self.total_energy

    def __hash__(self):
        return hash((self.state, self.total_energy))

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


def solve(start_state: State) -> SearchNode:
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
        if node.is_goal():
            return node
        for move, state, energy in node.state.successors():
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
        # for fl, fi, tl, ti in ((
        #         (Location.ROOM3, 0, Location.HALLWAY, 3),
        #         (Location.ROOM2, 0, Location.ROOM3, 0),
        #         (Location.ROOM2, 1, Location.HALLWAY, 5),
        #         (Location.HALLWAY, 3, Location.ROOM2, 1),
        #         (Location.ROOM4, 0, Location.HALLWAY, 7),
        #         (Location.ROOM4, 1, Location.HALLWAY, 9),
        #         (Location.HALLWAY, 7, Location.ROOM4, 1),
        #         (Location.HALLWAY, 5, Location.ROOM4, 0)
        #                        )):
        #     if fi == 5:
        #         breakpoint()
        #     next_state = state.apply(Move(from_position=Position(fl, fi), to_position=Position(tl, ti)))[0]
        #     if not any(s == next_state for _, s, _ in state.successors()):
        #         print("======== BAD ========")
        #         for _, s, _ in state.successors():
        #             print(str(s))
        #         exit(1)
        #     print(str(next_state))
        #     state = next_state
        solution = solve(state)
        print("==================[ SOLUTION ]==================")
        print(str(solution))

    @Challenge.register_part(1)
    def unfolded(self):
        with open(self.input_path, "r") as f:
            state = Part2State.parse(f.read())
        print(str(state))
        solution = solve(state)
        print("==================[ SOLUTION ]==================")
        print(str(solution))
