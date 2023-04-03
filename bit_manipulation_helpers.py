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


def byte_as_hex_str(byte: int) -> str:
    high_bits: int = (byte & 0xf0) >> 4
    low_bits: int = byte & 0xf

    result = f'0x{_4_bit_int_to_hex_char_map[high_bits]}{_4_bit_int_to_hex_char_map[low_bits]}'
    return result


def two_bytes_as_hex_str(hi_byte: int, lo_byte: int) -> str:
    hi_byte_high_bits: int = (hi_byte & 0xf0) >> 4
    hi_byte_low_bits: int = hi_byte & 0xf
    lo_byte_high_bits: int = (lo_byte & 0xf0) >> 4
    lo_byte_low_bits: int = lo_byte & 0xf

    result = f'0x{_4_bit_int_to_hex_char_map[hi_byte_high_bits]}{_4_bit_int_to_hex_char_map[hi_byte_low_bits]}{_4_bit_int_to_hex_char_map[lo_byte_high_bits]}{_4_bit_int_to_hex_char_map[lo_byte_low_bits]}'
    return result


def byte_as_bin_str(byte: int) -> str:
    bit_0 = (byte >> 7) & 1
    bit_1 = (byte >> 6) & 1
    bit_2 = (byte >> 5) & 1
    bit_3 = (byte >> 4) & 1
    bit_4 = (byte >> 3) & 1
    bit_5 = (byte >> 2) & 1
    bit_6 = (byte >> 1) & 1
    bit_7 = byte & 1

    result = f'{bit_0}{bit_1}{bit_2}{bit_3} {bit_4}{bit_5}{bit_6}{bit_7}'
    return result


def two_bytes_as_bin_str(hi_byte: int, lo_byte: int) -> str:
    bit_0 = (hi_byte >> 7) & 1
    bit_1 = (hi_byte >> 6) & 1
    bit_2 = (hi_byte >> 5) & 1
    bit_3 = (hi_byte >> 4) & 1
    bit_4 = (hi_byte >> 3) & 1
    bit_5 = (hi_byte >> 2) & 1
    bit_6 = (hi_byte >> 1) & 1
    bit_7 = hi_byte & 1

    bit_8 = (lo_byte >> 7) & 1
    bit_9 = (lo_byte >> 6) & 1
    bit_10 = (lo_byte >> 5) & 1
    bit_11 = (lo_byte >> 4) & 1
    bit_12 = (lo_byte >> 3) & 1
    bit_13 = (lo_byte >> 2) & 1
    bit_14 = (lo_byte >> 1) & 1
    bit_15 = lo_byte & 1
    result = f'{bit_0}{bit_1}{bit_2}{bit_3} {bit_4}{bit_5}{bit_6}{bit_7} {bit_8}{bit_9}{bit_10}{bit_11} {bit_12}{bit_13}{bit_14}{bit_15}'
    return result


def int_as_u16_hex_str(value: int) -> str:
    half_byte_1: int = value & 0b1111
    half_byte_2: int = (value >> 4) & 0b1111
    half_byte_3: int = (value >> 8) & 0b1111
    half_byte_4: int = (value >> 12) & 0b1111
    return f'0x{_4_bit_int_to_hex_char_map[half_byte_4]}{_4_bit_int_to_hex_char_map[half_byte_3]}{_4_bit_int_to_hex_char_map[half_byte_2]}{_4_bit_int_to_hex_char_map[half_byte_1]}'


def combine_bytes(lo_byte: int, hi_byte: int):
    result: int = hi_byte * 256 + lo_byte
    return result


def value_fits_in_two_bytes(value: int) -> bool:
    return (value >> 16) == 0


def value_fits_in_byte(value: int) -> bool:
    return (value >> 8) == 0