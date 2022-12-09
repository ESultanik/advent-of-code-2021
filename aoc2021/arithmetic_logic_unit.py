from enum import Enum
from typing import Dict, List, Union

import z3

from . import Challenge


Symbolic = z3.ExprRef
Variable = z3.z3.ArithRef


class Register(Enum):
    X = "x"
    Y = "y"
    Z = "z"
    W = "w"


class ALU:
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
        alu = ALU()
        alu.solver.push()
        with open(self.input_path, "r") as f:
            def parse_arg(arg: str) -> Union[int, Register]:
                try:
                    return int(arg)
                except ValueError:
                    pass
                for r in Register:
                    if r.value == arg:
                        return r
                raise ValueError()

            for line in f:
                print(line)
                cmd, raw_reg, *raw_args = line.split()
                reg = parse_arg(raw_reg)
                args = [parse_arg(arg) for arg in raw_args]
                match cmd:
                    case "inp":
                        assert len(args) == 0
                        alu.inp(reg)
                    case "add":
                        assert len(args) == 1
                        alu.add(reg, args[0])
                    case "mul":
                        assert len(args) == 1
                        alu.mul(reg, args[0])
                    case "div":
                        assert len(args) == 1
                        alu.div(reg, args[0])
                    case "mod":
                        assert len(args) == 1
                        alu.mod(reg, args[0])
                    case "eql":
                        assert len(args) == 1
                        alu.eql(reg, args[0])
                    case _:
                        raise ValueError(line)

        alu.simplify()
        alu.solver.add(alu.regs[Register.Z] == 0)
        value = 0
        for i in alu.inputs:
            value *= 10
            value += i
        if alu.solver.check(value > 99999999999991) == z3.sat:
            print(alu.solver.model())
        else:
            print("UNSAT")
