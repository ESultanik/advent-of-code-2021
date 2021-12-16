from abc import ABC, abstractmethod
from io import BytesIO, SEEK_CUR, SEEK_SET, SEEK_END
import itertools
from typing import Dict, IO, Iterable, Iterator, List, TextIO, Type, TypeVar

from . import Challenge


class HexStringStream(BytesIO):
    def __init__(self, hex_str: str):
        super().__init__(bytes.fromhex(hex_str))


class FileBackedHexStringStream(IO[bytes]):
    def __init__(self, hex_file: TextIO):
        super().__init__()
        if not hex_file.seekable():
            raise ValueError("hex_file must be seekable")
        elif not hex_file.readable():
            raise ValueError("hex_file must be readable")
        self.hex_file: TextIO = hex_file
        start_offset = hex_file.tell()
        self.offset: int = start_offset // 2
        try:
            hex_file.seek(0, SEEK_END)
            self.num_bytes = hex_file.tell() // 2
        finally:
            hex_file.seek(start_offset)

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    @property
    def mode(self) -> str:
        return "rb"

    @property
    def name(self) -> str:
        return self.hex_file.name

    def close(self):
        self.hex_file.close()

    @property
    def closed(self) -> bool:
        return self.hex_file.closed

    def fileno(self) -> int:
        return self.hex_file.fileno()

    def flush(self):
        self.hex_file.flush()

    def isatty(self) -> bool:
        return False

    def read(self, n: int = -1) -> bytes:
        self.hex_file.seek(self.offset * 2)
        if n == -1:
            return bytes.fromhex(self.hex_file.read())
        else:
            return bytes.fromhex(self.hex_file.read(n * 2))

    def readable(self) -> bool:
        return True

    def readline(self, limit: int = -1) -> bytes:
        raise NotImplementedError(f"{self.__class__.__name__} does not support readline")

    def readlines(self, hint: int = -1) -> List[bytes]:
        raise NotImplementedError(f"{self.__class__.__name__} does not support readlines")

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == SEEK_SET:
            new_offset = offset
        elif whence == SEEK_CUR:
            new_offset = self.offset + offset
        else:
            new_offset = self.num_bytes - offset
        new_offset = max(0, min(new_offset, self.num_bytes))
        self.offset = new_offset
        return new_offset

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.offset

    def truncate(self, size: int = None) -> int:
        raise NotImplementedError(f"{self.__class__.__name__} does not support truncate")

    def writable(self) -> bool:
        return False

    def write(self, s: bytes) -> int:
        raise NotImplementedError(f"{self.__class__.__name__} does not support write")

    def writelines(self, lines: List[bytes]) -> None:
        raise NotImplementedError(f"{self.__class__.__name__} does not support writelines")

    def __enter__(self) -> "FileBackedHexStringStream":
        return self

    @abstractmethod
    def __exit__(self, type, value, traceback):
        self.close()


class BitStream:
    def __init__(self, stream: IO[bytes]):
        if not stream.seekable():
            raise ValueError(f"stream must be seekable")
        elif not stream.readable():
            raise ValueError(f"stream must be readable")
        self.stream: IO[bytes] = stream
        old_offset = self.stream.tell()
        self.offset = old_offset * 8
        try:
            self.stream.seek(0, SEEK_END)
            self.bit_length: int = self.stream.tell() * 8
        finally:
            self.stream.seek(old_offset)

    def __bool__(self):
        return self.offset < self.bit_length - 1

    def read(self, num_bits: int) -> int:
        result = self.peek(num_bits)
        self.offset = min(self.bit_length, self.offset + num_bits)
        return result

    def peek(self, num_bits: int) -> int:
        self.stream.seek(self.offset // 8)
        bits_before = self.offset % 8
        num_bytes = (bits_before + num_bits) // 8
        if (bits_before + num_bits) % 8 != 0:
            num_bytes += 1
        bits_after = 8 * num_bytes - bits_before - num_bits
        data = self.stream.read(num_bytes)
        if len(data) < num_bytes:
            data = data + b"\0" * (num_bytes - len(data))
        value = int.from_bytes(data, byteorder="big", signed=False)
        value >>= bits_after
        if bits_before > 0:
            # mask out the bits_before most significant bits
            bit_mask = 2**num_bits - 1
            value &= bit_mask
        return value

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
        # print(f"Packet type {type_id} version {version}")
        if type_id not in PACKETS_BY_TYPE:
            raise NotImplementedError(f"Add support for packets of type {type_id}")
        else:
            p = PACKETS_BY_TYPE[type_id].parse_type(bits)
        setattr(p, "version", version)
        return p

    @abstractmethod
    def value(self) -> int:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def parse_type(cls: T, bits: BitStream) -> T:
        raise NotImplementedError()


class Literal(Packet):
    type_id = 4

    def __init__(self, number: int):
        self.number: int = number

    def value(self) -> int:
        return self.number

    @classmethod
    def parse_type(cls: T, bits: BitStream) -> T:
        number = 0
        last = False
        while not last:
            group = bits.read(5)
            last = not (group & 0b10000)
            number = (number << 4) | (group & 0b1111)
        # print(f"\tLiteral({number})")
        return Literal(number)


class Operator(Packet, ABC):
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
            # print(f"\tOperator with {num_subpackets} sub-packets")
            return cls((Packet.parse(bits) for _ in range(num_subpackets)))
        else:
            total_length = bits.read(15)
            # print(f"\tOperator with {total_length} bits of sub-packets")
            if bits.tell() + total_length >= bits.bit_length:
                raise ValueError("Not enough data for packet!")
            start_pos = bits.tell()
            subpackets = []
            while bits.tell() - start_pos < total_length:
                subpackets.append(Packet.parse(bits))
            return cls(subpackets)


class Sum(Operator):
    type_id = 0

    def value(self) -> int:
        return sum(p.value() for p in self.subpackets)


class Product(Operator):
    type_id = 1

    def value(self) -> int:
        prod = 1
        for p in self.subpackets:
            prod *= p.value()
        return prod


class Minimum(Operator):
    type_id = 2

    def value(self) -> int:
        return min(p.value() for p in self.subpackets)


class Maximum(Operator):
    type_id = 3

    def value(self) -> int:
        return max(p.value() for p in self.subpackets)


class GreaterThan(Operator):
    type_id = 5

    def value(self) -> int:
        return [0, 1][self.subpackets[0].value() > self.subpackets[1].value()]


class LessThan(Operator):
    type_id = 6

    def value(self) -> int:
        return [0, 1][self.subpackets[0].value() < self.subpackets[1].value()]


class Equals(Operator):
    type_id = 7

    def value(self) -> int:
        return [0, 1][self.subpackets[0].value() == self.subpackets[1].value()]


class PacketDecoder(Challenge):
    day = 16

    @Challenge.register_part(0)
    def versions(self):
        with open(self.input_path, "r") as f:
            bits = BitStream(FileBackedHexStringStream(f))
            # bits = BitStream(HexStringStream("38006F45291200"))
            # bits = BitStream(HexStringStream("EE00D40C823060"))
            version_sum = 0
            while bits and bits.peek(6):
                packet = Packet.parse(bits)
                version_sum += sum(p.version for p in packet)
        self.output.write(f"{version_sum}\n")

    @Challenge.register_part(1)
    def evaluate(self):
        with open(self.input_path, "r") as f:
            bits = BitStream(FileBackedHexStringStream(f))
            value = Packet.parse(bits).value()
        self.output.write(f"{value}\n")
