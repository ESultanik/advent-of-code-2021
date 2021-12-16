from abc import ABC, abstractmethod
import itertools
from typing import Dict, Iterable, Iterator, List, Type, TypeVar

from . import Challenge


class BitStream:
    def __init__(self, hex_str: str):
        self.bit_length: int = len(hex_str.strip()) * 4
        self.value: int = int(hex_str, 16)
        self.offset: int = 0

    def __bool__(self):
        return self.offset < self.bit_length - 1

    def read(self, num_bits: int) -> int:
        result = self.peek(num_bits)
        self.offset = min(self.bit_length, self.offset + num_bits)
        return result

    def peek(self, num_bits: int) -> int:
        mask = 0
        for _ in range(num_bits):
            mask = (mask << 1) | 0b1
        bits_after = self.bit_length - self.offset - num_bits
        if bits_after < 0:
            return (self.value << (bits_after * -1)) & mask
        else:
            return (self.value >> bits_after) & mask

    def tell(self):
        return self.offset

    def seek(self, offset: int):
        self.offset = max(0, min(offset, self.bit_length))


PACKETS_BY_TYPE: Dict[int, Type["Packet"]] = {}

T = TypeVar("T")


class Packet(ABC):
    type_id: int
    version: int

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, "type_id") and cls.type_id is not None:
            if cls.type_id in PACKETS_BY_TYPE:
                raise TypeError(f"A packet of type {cls.type_id} is already assigned to "
                                f"{PACKETS_BY_TYPE[cls.type_id].__name__}")
            PACKETS_BY_TYPE[cls.type_id] = cls

    def __iter__(self) -> "Packet":
        yield self

    @staticmethod
    def parse(bits: BitStream) -> "Packet":
        version = bits.read(3)
        type_id = bits.read(3)
        print(f"Packet type {type_id} version {version}")
        if type_id not in PACKETS_BY_TYPE:
            # raise NotImplementedError(f"Add support for packets of type {type_id}")
            # treat it as an operator for now
            p = Operator.parse_type(bits)
            setattr(p, "type_id", type_id)
        else:
            p = PACKETS_BY_TYPE[type_id].parse_type(bits)
        setattr(p, "version", version)
        return p

    @classmethod
    @abstractmethod
    def parse_type(cls: T, bits: BitStream) -> T:
        raise NotImplementedError()


class Literal(Packet):
    type_id = 4

    def __init__(self, number: int):
        self.number: int = number

    @classmethod
    def parse_type(cls: T, bits: BitStream) -> T:
        number = 0
        last = False
        while not last:
            group = bits.read(5)
            last = not (group & 0b10000)
            number = (number << 4) | (group & 0b1111)
        print(f"\tLiteral({number})")
        return Literal(number)


class Operator(Packet):
    def __init__(self, subpackets: Iterable[Packet]):
        self.subpackets: Tuple[Packet, ...] = tuple(subpackets)

    def __iter__(self) -> Iterator[Packet]:
        yield self
        yield from itertools.chain(*self.subpackets)

    @classmethod
    def parse_type(cls: T, bits: BitStream) -> T:
        length_type_id = bits.read(1)
        if length_type_id:
            num_subpackets = bits.read(11)
            print(f"\tOperator with {num_subpackets} sub-packets")
            return Operator((Packet.parse(bits) for _ in range(num_subpackets)))
        else:
            total_length = bits.read(15)
            print(f"\tOperator with {total_length} bits of sub-packets")
            if bits.tell() + total_length >= bits.bit_length:
                raise ValueError("Not enough data for packet!")
            start_pos = bits.tell()
            subpackets = []
            while bits.tell() - start_pos < total_length:
                subpackets.append(Packet.parse(bits))
            return Operator(subpackets)


class PacketDecoder(Challenge):
    day = 16

    @Challenge.register_part(0)
    def versions(self):
        with open(self.input_path, "r") as f:
            bits = BitStream(f.read())
        # bits = BitStream("38006F45291200")
        # bits = BitStream("EE00D40C823060")
        version_sum = 0
        while bits and bits.peek(6):
            packet = Packet.parse(bits)
            version_sum += sum(p.version for p in packet)
        self.output.write(f"{version_sum}\n")
