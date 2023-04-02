from bit_manipulation_helpers import convert_to_s8, convert_to_s16


class ByteReader:
    def __init__(self, bytes_array: bytes):
        self.bytes_array: bytes = bytes_array
        self.index = 0

    def peek_as_u8(self, offset: int = 0) -> int:
        assert 0 <= self.index + offset < len(self.bytes_array), 'Attempting to peek outside bytes'
        result: int = self.bytes_array[self.index + offset]
        return result

    def read_next_byte_as_u8(self) -> int:
        assert self.index < len(self.bytes_array), 'Attempting to read past last byte'
        result: int = self.bytes_array[self.index]
        self.index += 1
        return result

    def read_next_byte_as_s8(self) -> int:
        assert self.index < len(self.bytes_array), 'Attempting to read past last byte'
        result: int = self.bytes_array[self.index]
        self.index += 1
        return convert_to_s8(result)

    def read_next_two_byte_as_u16(self) -> int:
        assert self.index < len(self.bytes_array) - 1, 'Attempting to read past last byte'
        lo_byte: int = self.bytes_array[self.index]
        hi_byte: int = self.bytes_array[self.index + 1]
        result: int = hi_byte * 256 + lo_byte
        self.index += 2
        return result

    def read_next_two_byte_as_s16(self) -> int:
        assert self.index < len(self.bytes_array) - 1, 'Attempting to read past last byte'
        lo_byte: int = self.bytes_array[self.index]
        hi_byte: int = self.bytes_array[self.index + 1]
        result: int = hi_byte * 256 + lo_byte
        self.index += 2
        return convert_to_s16(result)

    def read_one_or_two_bytes_as_u8_or_u16(self, is_word) -> int:
        return self.read_next_two_byte_as_u16() if is_word else self.read_next_byte_as_u8()

    def read_one_or_two_bytes_as_s8_or_s16(self, is_word) -> int:
        return self.read_next_two_byte_as_s16() if is_word else self.read_next_byte_as_s8()

    def seek(self, index: int) -> None:
        self.index = index

    def is_at_end(self) -> bool:
        return self.index == len(self.bytes_array)
