from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import z3

from . import Challenge


Symbolic = z3.ExprRef
Variable = z3.z3.ArithRef


class Register(Enum):
    X = "x"
    Y = "y"
    Z = "z"
    W = "w"


class Opcode(Enum):
    ADD = "add"
    MULTIPLY = "mul"
    DIVIDE = "div"
    MODULUS = "mod"
    EQUAL = "eql"
    INPUT = "inp"


@dataclass(frozen=True)
class Instruction:
    opcode: Opcode
    register: Register
    operand: Optional[Union[Register, int]]

    @staticmethod
    def parse_arg(arg: str) -> Union[int, Register]:
        try:
            return int(arg)
        except ValueError:
            pass
        for r in Register:
            if r.value == arg:
                return r
        raise ValueError()

    @classmethod
    def parse(cls, line: str) -> "Instruction":
        cmd, raw_reg, *raw_args = line.split()
        reg = Instruction.parse_arg(raw_reg)
        args = [Instruction.parse_arg(a) for a in raw_args]
        if len(args) > 1:
            raise ValueError(f"Too many operands: {line!r}")
        for op in Opcode:
            if cmd == op.value:
                break
        else:
            raise ValueError(f"Invalid opcode {cmd!r} in {line!r}")
        if not args:
            arg: Optional[Union[Register, int]] = None
        else:
            arg = args[0]
        return cls(opcode=op, register=reg, operand=arg)

    def __str__(self):
        if self.operand is not None:
            if isinstance(self.operand, Register):
                opval = self.operand.value
            else:
                opval = str(self.operand)
            return f"{self.opcode.value} {self.register.value} {opval}"
        else:
            return f"{self.opcode.value} {self.register.value}"


@dataclass(frozen=True)
class Program:
    instructions: Sequence[Instruction]

    @classmethod
    def parse(cls, path: Path):
        with open(path, "r") as f:
            return Program(tuple(map(Instruction.parse, f)))


class Interpreter(ABC):
    @abstractmethod
    def execute(self, instruction: Instruction):
        raise NotImplementedError()

    @abstractmethod
    def run(self, program: Program):
        raise NotImplementedError()


class BackwardSolver(Interpreter):
    def __init__(self):
        self.regs: Dict[Register, Union[int, Symbolic]] = {
            Register.W: z3.Int("finalw"),
            Register.X: z3.Int("finalx"),
            Register.Y: z3.Int("finaly"),
            Register.Z: 0
        }
        self._var_counter: int = 0
        self.inputs: List[Variable] = []
        self.solver = z3.Solver()
        self.solver.push()

    def solve(self, min_value: Optional[int] = None) -> Optional[int]:
        if min_value is not None:
            val = 0
            for i in self.inputs:
                val *= 10
                if val == 0:
                    val = i
                else:
                    val += i
            result = self.solver.check(val > min_value)
        else:
            result = self.solver.check()
        if result == z3.sat:
            model = self.solver.model()
            v = 0
            for i in self.inputs:
                v *= 10
                v += model[i].as_long()
            return v
        else:
            return None

    def maximum_input(self) -> int:
        feasible = self.solve()
        if feasible is None:
            raise ValueError("No solutions found!")
        print(feasible)
        while True:
            bigger = self.solve(min_value=feasible)
            if bigger is None:
                return feasible
            print(bigger)
            assert bigger > feasible
            feasible = bigger

    def new_version(self, reg: Register) -> Symbolic:
        var = z3.Int(f"{reg.value}{self._var_counter}")
        self._var_counter += 1
        self.regs[reg] = var
        return var

    def new_input(self) -> Symbolic:
        var = z3.Int(f"inp{len(self.inputs)}")
        self.inputs.insert(0, var)
        self.solver.add(var >= 1)
        self.solver.add(var <= 9)
        return var

    def execute(self, instruction: Instruction):
        result = self.regs[instruction.register]
        if isinstance(instruction.operand, Register):
            operand = self.regs[instruction.operand]
        else:
            operand = instruction.operand
        if isinstance(result, int) and result == 0 and instruction.opcode == Opcode.ADD:
            self.solver.add(operand == 0)
            return
        elif isinstance(result, int) and result == 1 and instruction.opcode == Opcode.MULTIPLY:
            self.solver.add(operand == 1)
            return
        prev_version = self.new_version(instruction.register)
        if instruction.opcode == Opcode.ADD:
            self.solver.add(result == prev_version + operand)
        elif instruction.opcode == Opcode.MULTIPLY:
            self.solver.add(result == prev_version * operand)
        elif instruction.opcode == Opcode.DIVIDE:
            self.solver.add(result == prev_version / operand)
            self.solver.add(operand != 0)
        elif instruction.opcode == Opcode.MODULUS:
            self.solver.add(result == prev_version % operand)
            self.solver.add(prev_version >= 0)
            self.solver.add(operand > 0)
        elif instruction.opcode == Opcode.INPUT:
            self.solver.add(result == self.new_input())
        elif instruction.opcode == Opcode.EQUAL:
            self.solver.add(result == z3.If(prev_version == operand, 1, 0))
            return
            can_be_zero = self.solver.check(result == 0) == z3.sat
            can_be_one = self.solver.check(result == 1) == z3.sat
            if can_be_one and not can_be_zero:
                print(f"{instruction!s} is always true!")
                self.solver.add(prev_version == operand)
            elif can_be_zero and not can_be_one:
                print(f"{instruction!s} is always false!")
                self.solver.add(prev_version != operand)
            else:
                print(f"{instruction!s} is undetermined...")
                self.solver.add(result == z3.If(prev_version == operand, 1, 0))

    def run(self, program: Program):
        for inst in reversed(program.instructions):
            # interpret the program in reverse
            self.execute(inst)


class ALU(Interpreter):
    def __init__(self):
        self.regs: Dict[Register, Union[int, Symbolic]] = {
            Register.W: 0,
            Register.X: 0,
            Register.Y: 0,
            Register.Z: 0
        }
        self.inputs: List[Variable] = []
        self.solver = z3.Solver()
        self._had_undetermined_equ: bool = False

    def simplify(self):
        for reg, value in list(self.regs.items()):
            if not isinstance(value, int):
                self.regs[reg] = z3.simplify(value)

    def execute(self, instruction: Instruction):
        if not hasattr(self, instruction.opcode.value):
            raise ValueError(f"Invalid opcode: {instruction.opcode}")
        if instruction.operand is not None:
            args = [instruction.operand]
        else:
            args = []
        getattr(self, instruction.opcode.value)(instruction.register, *args)

    def run(self, program: Program):
        for instruction in program.instructions:
            self.execute(instruction)

    def inp(self, reg: Register) -> Variable:
        var = z3.Int(f"inp{len(self.inputs)}")
        self.inputs.append(var)
        self.solver.add(var >= 1)
        self.solver.add(var <= 9)
        self.regs[reg] = var
        return var

    def mul(self, reg: Register, arg: Union[int, Register]):
        if isinstance(arg, Register):
            arg = self.regs[arg]
        self.regs[reg] = self.regs[reg] * arg

    def add(self, reg: Register, arg: Union[int, Register]):
        if isinstance(arg, Register):
            arg = self.regs[arg]
        self.regs[reg] = self.regs[reg] + arg

    def mod(self, reg: Register, arg: Union[int, Register]):
        a = self.regs[reg]
        if not isinstance(a, int):
            self.solver.add(a >= 0)
        if isinstance(arg, int):
            b = arg
        else:
            b = self.regs[arg]
            if not isinstance(b, int):
                self.solver.add(b > 0)
        self.regs[reg] = a % b

    def div(self, reg: Register, arg: Union[int, Register]):
        if isinstance(arg, int):
            b = arg
        else:
            b = self.regs[arg]
            if not isinstance(b, int):
                self.solver.add(b != 0)
        a = self.regs[reg]
        if not isinstance(a, int) or not isinstance(b, int):
            self.regs[reg] = a / b
        else:
            self.regs[reg] = a // b

    def eql(self, reg: Register, arg: Union[int, Register]):
        a = self.regs[reg]
        if isinstance(arg, int):
            b = arg
        else:
            b = self.regs[arg]
        if isinstance(a, int) and isinstance(b, int):
            self.regs[reg] = [0, 1][a == b]
        else:
            self.regs[reg] = z3.If(a == b, 1, 0)
        if not self._had_undetermined_equ:
            self.simplify()
            can_be_zero = self.solver.check(self.regs[reg] == 0) == z3.sat
            can_be_one = self.solver.check(self.regs[reg] == 1) == z3.sat
            if can_be_one and not can_be_zero:
                print(f"eql {reg} {arg} is always true!")
                self.regs[reg] = 1
            elif can_be_zero and not can_be_one:
                print(f"eql {reg} {arg} is always false!")
                self.regs[reg] = 0
            else:
                print(f"eql {reg} {arg} is undetermined...")
                self._had_undetermined_equ = True


class ArithmeticLogicUnit(Challenge):
    day = 24

    @Challenge.register_part(0)
    def largest_model_number(self):
        alu = BackwardSolver()
        program = Program.parse(self.input_path)
        alu.run(program)
        alu.maximum_input()
