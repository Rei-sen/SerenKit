from __future__ import annotations

from struct import calcsize, unpack_from
from typing import Any, cast


def padding(size: int) -> bytes:
    return bytes(size) if size > 0 else b""


class BinaryReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.length = len(data)

    def read_struct(self, fmt: str) -> Any:
        size = calcsize(fmt)
        if self.pos + size > self.length:
            raise EOFError("End of stream")

        result = unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return result[0] if len(result) == 1 else result

    def read_byte(self, signed: bool = False) -> int:
        return cast(int, self.read_struct("<b" if signed else "<B"))

    def read_bool(self) -> bool:
        return cast(bool, self.read_struct("<?"))

    def read_uint16(self) -> int:
        return cast(int, self.read_struct("<H"))

    def read_uint32(self) -> int:
        return cast(int, self.read_struct("<I"))

    def read_float(self) -> float:
        return cast(float, self.read_struct("<f"))

    def read_int_array(self, length: int, fmt: str = "I") -> list[int]:
        return [cast(int, self.read_struct(f"<{fmt}")) for _ in range(length)]

    def read_float_array(self, length: int) -> list[float]:
        return [cast(float, self.read_struct("<f")) for _ in range(length)]

    def read_bytes(self, length: int) -> bytes:
        if self.pos + length > self.length:
            raise EOFError("End of stream")
        value = self.data[self.pos : self.pos + length]
        self.pos += length
        return value
