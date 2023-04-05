import enum


class BitIndexDirection(enum.Enum):
    FROM_RIGHT = 1
    FROM_LEFT = 2


def is_bit_set(value: int, bit_index, bit_index_direction: BitIndexDirection) -> bool:
    if bit_index_direction == BitIndexDirection.FROM_RIGHT:
        return (value >> bit_index & 1) > 0
    return (value >> (7 - bit_index) & 1) > 0


def get_bits_from_byte(value: int, bit_index: int, count: int, bit_index_direction: BitIndexDirection):
    if bit_index_direction == BitIndexDirection.FROM_RIGHT:
        result = value >> (bit_index + 1 - count)
    else:
        result = value >> (8 - (count + bit_index))

    match count:
        case 1:
            return result & 0b1
        case 2:
            return result & 0b11
        case 3:
            return result & 0b111
        case 4:
            return result & 0b1111
        case 5:
            return result & 0b11111
        case 6:
            return result & 0b111111
        case 7:
            return result & 0b1111111
        case 8:
            return result & 0b11111111
        case _:
            assert False, f'Must get between 1 and 8 bytes inclusive not {count}'


def convert_to_s8(unsigned_value: int):
    unsigned_value &= 0xff
    return unsigned_value - 256 if unsigned_value >= 128 else unsigned_value


def convert_to_s16(unsigned_value: int):
    unsigned_value &= 0xffff
    return unsigned_value - 65536 if unsigned_value >= 32768 else unsigned_value


_4_bit_int_to_hex_char_map: dict[int, str] = {
    0: '0',
    1: '1',
    2: '2',
    3: '3',
    4: '4',
    5: '5',
    6: '6',
    7: '7',
    8: '8',
    9: '9',
    10: 'A',
    11: 'B',
    12: 'C',
    13: 'D',
    14: 'E',
    15: 'F',
}


def int_as_u16_hex_str(value: int) -> str:
    half_byte_1: int = value & 0b1111
    half_byte_2: int = (value >> 4) & 0b1111
    half_byte_3: int = (value >> 8) & 0b1111
    half_byte_4: int = (value >> 12) & 0b1111
    return f'0x{_4_bit_int_to_hex_char_map[half_byte_4]}{_4_bit_int_to_hex_char_map[half_byte_3]}{_4_bit_int_to_hex_char_map[half_byte_2]}{_4_bit_int_to_hex_char_map[half_byte_1]}'

