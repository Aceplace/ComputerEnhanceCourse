from __future__ import annotations
import enum
import sys
from typing import Dict, Optional, Union
from io import StringIO
from bit_manipulation_helpers import get_bits_from_byte, BitIndexDirection, is_bit_set
from byte_reader import ByteReader


class RegisterMnemonic(enum.Enum):
    NONE = 0
    AL = enum.auto()
    AH = enum.auto()
    AX = enum.auto()
    BL = enum.auto()
    BH = enum.auto()
    BX = enum.auto()
    CL = enum.auto()
    CH = enum.auto()
    CX = enum.auto()
    DL = enum.auto()
    DH = enum.auto()
    DX = enum.auto()
    SP = enum.auto()
    BP = enum.auto()
    SI = enum.auto()
    DI = enum.auto()
    CS = enum.auto()
    DS = enum.auto()
    SS = enum.auto()
    ES = enum.auto()

    def __str__(self):
        return self.name.lower()


reg_to_register_type_w0_map: Dict[int, RegisterMnemonic] = {
    0b000: RegisterMnemonic.AL,
    0b001: RegisterMnemonic.CL,
    0b010: RegisterMnemonic.DL,
    0b011: RegisterMnemonic.BL,
    0b100: RegisterMnemonic.AH,
    0b101: RegisterMnemonic.CH,
    0b110: RegisterMnemonic.DH,
    0b111: RegisterMnemonic.BH,
}

reg_to_register_type_w1_map: Dict[int, RegisterMnemonic] = {
    0b000: RegisterMnemonic.AX,
    0b001: RegisterMnemonic.CX,
    0b010: RegisterMnemonic.DX,
    0b011: RegisterMnemonic.BX,
    0b100: RegisterMnemonic.SP,
    0b101: RegisterMnemonic.BP,
    0b110: RegisterMnemonic.SI,
    0b111: RegisterMnemonic.DI,
}

sr_to_register_type_map: Dict[int, RegisterMnemonic] = {
    0b000: RegisterMnemonic.ES,
    0b001: RegisterMnemonic.CS,
    0b010: RegisterMnemonic.SS,
    0b011: RegisterMnemonic.DS,
}


def get_register_from_reg(reg: int, word_bit_set: bool) -> RegisterMnemonic:
    if word_bit_set:
        return reg_to_register_type_w1_map[reg]
    else:
        return reg_to_register_type_w0_map[reg]


class DisplacementType(enum.Enum):
    NONE = 0
    EIGHT_BIT = enum.auto
    SIXTEEN_BIT = enum.auto


class EffectiveAddressCalculation:
    direct_address: EffectiveAddressCalculation = None

    def __init__(self, is_direct_address: bool, register_one: RegisterMnemonic, register_two: RegisterMnemonic, displacement_type: DisplacementType):
        self.is_direct_address = is_direct_address
        self.register_one = register_one
        self.register_two = register_two
        self.displacement_type = displacement_type

    def has_displacement(self):
        return self.displacement_type is not DisplacementType.NONE


EffectiveAddressCalculation.direct_address = EffectiveAddressCalculation(True, RegisterMnemonic.NONE, RegisterMnemonic.NONE, DisplacementType.NONE)

r_m_to_effective_address_calculation_mod_00_map: Dict[int, EffectiveAddressCalculation] = {
    0b000: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.SI, DisplacementType.NONE),
    0b001: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.DI, DisplacementType.NONE),
    0b010: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.SI, DisplacementType.NONE),
    0b011: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.DI, DisplacementType.NONE),
    0b100: EffectiveAddressCalculation(False, RegisterMnemonic.SI, RegisterMnemonic.NONE, DisplacementType.NONE),
    0b101: EffectiveAddressCalculation(False, RegisterMnemonic.DI, RegisterMnemonic.NONE, DisplacementType.NONE),
    0b110: EffectiveAddressCalculation.direct_address,
    0b111: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.NONE, DisplacementType.NONE),
}

r_m_to_effective_address_calculation_mod_01_map: Dict[int, EffectiveAddressCalculation] = {
    0b000: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.SI, DisplacementType.EIGHT_BIT),
    0b001: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.DI, DisplacementType.EIGHT_BIT),
    0b010: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.SI, DisplacementType.EIGHT_BIT),
    0b011: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.DI, DisplacementType.EIGHT_BIT),
    0b100: EffectiveAddressCalculation(False, RegisterMnemonic.SI, RegisterMnemonic.NONE, DisplacementType.EIGHT_BIT),
    0b101: EffectiveAddressCalculation(False, RegisterMnemonic.DI, RegisterMnemonic.NONE, DisplacementType.EIGHT_BIT),
    0b110: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.NONE, DisplacementType.EIGHT_BIT),
    0b111: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.NONE, DisplacementType.EIGHT_BIT),
}

r_m_to_effective_address_calculation_mod_10_map: Dict[int, EffectiveAddressCalculation] = {
    0b000: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.SI, DisplacementType.SIXTEEN_BIT),
    0b001: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.DI, DisplacementType.SIXTEEN_BIT),
    0b010: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.SI, DisplacementType.SIXTEEN_BIT),
    0b011: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.DI, DisplacementType.SIXTEEN_BIT),
    0b100: EffectiveAddressCalculation(False, RegisterMnemonic.SI, RegisterMnemonic.NONE, DisplacementType.SIXTEEN_BIT),
    0b101: EffectiveAddressCalculation(False, RegisterMnemonic.DI, RegisterMnemonic.NONE, DisplacementType.SIXTEEN_BIT),
    0b110: EffectiveAddressCalculation(False, RegisterMnemonic.BP, RegisterMnemonic.NONE, DisplacementType.SIXTEEN_BIT),
    0b111: EffectiveAddressCalculation(False, RegisterMnemonic.BX, RegisterMnemonic.NONE, DisplacementType.SIXTEEN_BIT),
}


class EffectiveAddress:
    def __init__(self, effective_address_calculation: EffectiveAddressCalculation, displacement: Optional[int]):
        self.effective_address_calculation = effective_address_calculation
        self.displacement = displacement

    def __str__(self) -> str:
        return self._get_decode_str_with_displacement()

    def _get_decode_str_with_displacement(self):
        if self.effective_address_calculation.is_direct_address:
            assert self.displacement is not None, 'Need a displacement for direct address'
            return f'[{self.displacement}]'

        if self.displacement is not None:
            displacement_str_part: str = f'+ {self.displacement}' if self.displacement >= 0 else f'- {abs(self.displacement)}'
            if self.effective_address_calculation.register_two is not RegisterMnemonic.NONE:
                return f'[{self.effective_address_calculation.register_one} + {self.effective_address_calculation.register_two} {displacement_str_part}]'
            else:
                return f'[{self.effective_address_calculation.register_one} {displacement_str_part}]'

        if self.effective_address_calculation.register_two is not RegisterMnemonic.NONE:
            return f'[{self.effective_address_calculation.register_one} + {self.effective_address_calculation.register_two}]'
        else:
            return f'[{self.effective_address_calculation.register_one}]'


def get_effective_address_calculation_from_r_m_mod(r_m: int, mod: int) -> EffectiveAddressCalculation:
    assert mod != 0b11, 'Register to Register mode does not use effective address'
    if mod == 0b00:  # no displacement
        return r_m_to_effective_address_calculation_mod_00_map[r_m]
    elif mod == 0b01:  # 8 bit offset
        return r_m_to_effective_address_calculation_mod_01_map[r_m]
    return r_m_to_effective_address_calculation_mod_10_map[r_m]  # 16 bit offset


def explicit_applied_immediate_value_str(value: int, is_word: bool) -> str:
    return f'word  {value}' if is_word else f'byte  {value}'


class InstructionType(enum.Enum):
    NONE = 0
    MOV = enum.auto()
    ADD = enum.auto()
    SUB = enum.auto()
    CMP = enum.auto()
    JO = enum.auto()
    JNO = enum.auto()
    JB = enum.auto()
    JAE = enum.auto()
    JE = enum.auto()
    JNE = enum.auto()
    JBE = enum.auto()
    JA = enum.auto()
    JS = enum.auto()
    JNS = enum.auto()
    JP = enum.auto()
    JNP = enum.auto()
    JL = enum.auto()
    JGE = enum.auto()
    JLE = enum.auto()
    JG = enum.auto()
    LOOPNE = enum.auto()
    LOOPE = enum.auto()
    LOOP = enum.auto()
    JCXZ = enum.auto()

    def __str__(self):
        return self.name.lower()


opcodes_to_jmp_instructions_map: Dict[int, InstructionType] = {
    112: InstructionType.JO,
    113: InstructionType.JNO,
    114: InstructionType.JB,
    115: InstructionType.JAE,
    116: InstructionType.JE,
    117: InstructionType.JNE,
    118: InstructionType.JBE,
    119: InstructionType.JA,
    120: InstructionType.JS,
    121: InstructionType.JNS,
    122: InstructionType.JP,
    123: InstructionType.JNP,
    124: InstructionType.JL,
    125: InstructionType.JGE,
    126: InstructionType.JLE,
    127: InstructionType.JG,
    224: InstructionType.LOOPNE,
    225: InstructionType.LOOPE,
    226: InstructionType.LOOP,
    227: InstructionType.JCXZ,
}

opcodes_for_jmp_instruction: list[int] = [opcode for opcode in opcodes_to_jmp_instructions_map.keys()]


class OperandType(enum.Enum):
    NONE = 0
    REGISTER = enum.auto()
    EFFECTIVE_ADDRESS = enum.auto()
    LITERAL_VALUE_OFFSET = enum.auto()
    LITERAL_VALUE_BYTE = enum.auto()
    LITERAL_VALUE_WORD = enum.auto()

    def is_immediate_value(self):
        return self in [OperandType.LITERAL_VALUE_BYTE, OperandType.LITERAL_VALUE_WORD]

    def is_reg_or_effective_address(self):
        return self in [OperandType.REGISTER, OperandType.EFFECTIVE_ADDRESS]


class Operand:
    def __init__(self, operand_type: OperandType = OperandType.NONE, value: Union[RegisterMnemonic, EffectiveAddress, int, None] = None):
        self.operand_type: OperandType = operand_type
        self.value: Union[RegisterMnemonic, EffectiveAddressCalculation, int, None] = value

    def __str__(self):
        if self.operand_type is not OperandType.LITERAL_VALUE_OFFSET:
            return str(self.value)
        relative_adjusted_value = self.value + 2  # have to adjust encode value because nasm automatically subtracts 2 in its $ synstax
        sign: str = '+' if relative_adjusted_value >= 0 else '-'
        return f'${sign}{abs(relative_adjusted_value)}'


class Operation:
    def __init__(self):
        self.instruction_type: InstructionType = InstructionType.NONE
        self.operand_one: Operand = Operand()
        self.operand_two: Operand = Operand()

    def __str__(self):
        return self.get_decode_str()

    def __repr__(self):
        return f'op({self.get_decode_str()})'

    def get_decode_str(self):
        operand_two_str: str = ''
        if self.operand_two.operand_type.is_immediate_value():
            immediate_value: int = self.operand_two.value
            #  check for whether an explicit immediate value is required
            if self.operand_one.operand_type == OperandType.EFFECTIVE_ADDRESS:
                is_word: bool = self.operand_two.operand_type == OperandType.LITERAL_VALUE_WORD
                operand_two_str = f', word  {immediate_value}' if is_word else f', byte  {immediate_value}'
            else:
                operand_two_str = f', {immediate_value}'
        elif self.operand_two.operand_type.is_reg_or_effective_address():
            operand_two_str = f', {self.operand_two.value}'

        return f'{self.instruction_type} {self.operand_one}{operand_two_str}'


def create_literal_value_operand(value: int, is_word: bool):
    result: Operand = Operand()
    result.operand_type = OperandType.LITERAL_VALUE_WORD if is_word else OperandType.LITERAL_VALUE_BYTE
    result.value = value
    return result


def create_literal_value_offset_operand(value: int):
    result: Operand = Operand()
    result.operand_type = OperandType.LITERAL_VALUE_OFFSET
    result.value = value
    return result


def create_register_operand(register_type: RegisterMnemonic):
    result: Operand = Operand()
    result.operand_type = OperandType.REGISTER
    result.value = register_type
    return result


def create_effective_address_operand(effective_address_calculation: EffectiveAddressCalculation, displacement: Optional[int]):
    result: Operand = Operand()
    result.operand_type = OperandType.EFFECTIVE_ADDRESS
    result.value = EffectiveAddress(effective_address_calculation, displacement)
    return result


def decode(byte_reader: ByteReader) -> list[Operation]:
    operations: list[Operation] = []
    while not byte_reader.is_at_end():
        current_byte: int = byte_reader.peek_as_u8()

        operation: Operation
        if contains_mov_opcode(current_byte):
            operation = handle_mov_instruction(byte_reader)
        elif contains_add_sub_cmp_opcode(current_byte):
            operation = handle_add_sub_cmp_instruction(byte_reader)
        elif contains_jmp_opcode(current_byte):
            operation = handle_jmp_instruction(byte_reader)
        else:
            assert False, f'Unknown opcode {current_byte}'

        operations.append(operation)
    return operations


def read_displacement_if_has_any(byte_reader: ByteReader, mod: int, r_m: int) -> Optional[int]:
    displacement: Optional[int]
    if mod > 0:  # has displacement
        if mod == 0b10:  # 16 bit displacement
            displacement = byte_reader.read_next_two_byte_as_s16()
        else:  # 8 bit displacement
            displacement = byte_reader.read_next_byte_as_s8()
    elif r_m == 0b110:  # 16 bit displacement
        displacement = byte_reader.read_next_two_byte_as_s16()
    else:
        displacement = None
    return displacement


def get_mod_reg_r_m_from_byte(current_byte: int) -> (int, int, int):
    mod: int = get_bits_from_byte(current_byte, 0, 2, BitIndexDirection.FROM_LEFT)
    reg: int = get_bits_from_byte(current_byte, 2, 3, BitIndexDirection.FROM_LEFT)
    r_m: int = get_bits_from_byte(current_byte, 2, 3, BitIndexDirection.FROM_RIGHT)
    return mod, reg, r_m


class ImmToMemRegType(enum.Enum):
    NONE = 0
    BYTE = enum.auto()
    WORD = enum.auto()


def handle_operands_for_imm_to_reg_mem(byte_reader: ByteReader, possible_sign_extension: bool) -> (Operand, Operand):
    opcode_byte: int = byte_reader.peek_as_u8(-1)
    current_byte = byte_reader.read_next_byte_as_u8()
    mod, reg, r_m = get_mod_reg_r_m_from_byte(current_byte)

    operand_one: Operand
    operand_two: Operand

    if possible_sign_extension:
        sm_bits: int = get_bits_from_byte(opcode_byte, 1, 2, BitIndexDirection.FROM_RIGHT)
        immediate_value_is_word: bool = sm_bits == 0b01
        extended_value_present: bool = sm_bits == 0b01 or sm_bits == 0b11
    else:
        immediate_value_is_word: bool = is_bit_set(opcode_byte, 0, BitIndexDirection.FROM_RIGHT)
        extended_value_present: bool = False

    if mod == 0b11:  # immediate to register
        w_bit_set: bool = is_bit_set(opcode_byte, 0, BitIndexDirection.FROM_RIGHT)
        dst_register: RegisterMnemonic = get_register_from_reg(r_m, w_bit_set)
        immediate_value: int = byte_reader.read_one_or_two_bytes_as_u8_or_u16(immediate_value_is_word)

        operand_one = create_register_operand(dst_register)
        operand_two = create_literal_value_operand(immediate_value, immediate_value_is_word)
    else:  # immediate to memory
        displacement: Optional[int] = read_displacement_if_has_any(byte_reader, mod, r_m)
        effective_address_calculation: EffectiveAddressCalculation = get_effective_address_calculation_from_r_m_mod(r_m, mod)
        immediate_value: int = byte_reader.read_one_or_two_bytes_as_u8_or_u16(immediate_value_is_word)

        operand_one = create_effective_address_operand(effective_address_calculation, displacement)
        operand_two = create_literal_value_operand(immediate_value, immediate_value_is_word or extended_value_present)
    return operand_one, operand_two


def handle_operands_for_reg_mem_to_from_reg_mem(byte_reader: ByteReader) -> (Operand, Operand):
    opcode: int = byte_reader.peek_as_u8(-1)
    dst_bit_set: bool = is_bit_set(opcode, 1, BitIndexDirection.FROM_RIGHT)
    word_bit_set: bool = is_bit_set(opcode, 0, BitIndexDirection.FROM_RIGHT)

    current_byte = byte_reader.read_next_byte_as_u8()
    mod, reg, r_m = get_mod_reg_r_m_from_byte(current_byte)

    operand_one: Operand
    operand_two: Operand
    if mod == 0b11:  # register to register
        if opcode == 0b10001110:  # register to segment register
            src_register: RegisterMnemonic = get_register_from_reg(r_m, True)
            dst_register: RegisterMnemonic = sr_to_register_type_map[reg]
        elif opcode == 0b10001100:  # segment register to register
            src_register: RegisterMnemonic = sr_to_register_type_map[reg]
            dst_register: RegisterMnemonic = get_register_from_reg(r_m, True)
        else:  # register to register
            if not dst_bit_set:
                src_register: RegisterMnemonic = get_register_from_reg(reg, word_bit_set)
                dst_register: RegisterMnemonic = get_register_from_reg(r_m, word_bit_set)
            else:
                src_register: RegisterMnemonic = get_register_from_reg(r_m, word_bit_set)
                dst_register: RegisterMnemonic = get_register_from_reg(reg, word_bit_set)

        operand_one = create_register_operand(dst_register)
        operand_two = create_register_operand(src_register)
    elif mod == 0b00 and r_m == 0b110:  # direct address mode
        effective_address_calculation: EffectiveAddressCalculation = get_effective_address_calculation_from_r_m_mod(r_m, mod)
        dst_register: RegisterMnemonic = get_register_from_reg(reg, word_bit_set)
        memory_address: int = byte_reader.read_next_two_byte_as_u16()

        operand_one = create_register_operand(dst_register)
        operand_two = create_effective_address_operand(effective_address_calculation, memory_address)
    else:  # memory mode
        displacement: Optional[int] = read_displacement_if_has_any(byte_reader, mod, r_m)
        effective_address_calculation: EffectiveAddressCalculation = get_effective_address_calculation_from_r_m_mod(r_m, mod)
        register: RegisterMnemonic = get_register_from_reg(reg, word_bit_set)
        if dst_bit_set:  # memory to register
            operand_one = create_register_operand(register)
            operand_two = create_effective_address_operand(effective_address_calculation, displacement)
        else:  # register to memory
            operand_one = create_effective_address_operand(effective_address_calculation, displacement)
            operand_two = create_register_operand(register)
    return operand_one, operand_two


# def handle_operands_for_reg_mem_to_from_reg_mem(byte_reader: ByteReader) -> (Operand, Operand):
#     current_byte: int = byte_reader.peek_as_u8(-1)
#     dst_bit_set: bool = is_bit_set(current_byte, 1, BitIndexDirection.FROM_RIGHT)
#     word_bit_set: bool = is_bit_set(current_byte, 0, BitIndexDirection.FROM_RIGHT)
#     current_byte = byte_reader.read_next_byte_as_u8()
#     mod, reg, r_m = get_mod_reg_r_m_from_byte(current_byte)
#
#     operand_one: Operand
#     operand_two: Operand
#     if mod == 0b11:  # register to register
#         if not dst_bit_set:
#             src_register: RegisterType = get_register_from_reg(reg, word_bit_set)
#             dst_register: RegisterType = get_register_from_reg(r_m, word_bit_set)
#         else:
#             src_register: RegisterType = get_register_from_reg(r_m, word_bit_set)
#             dst_register: RegisterType = get_register_from_reg(reg, word_bit_set)
#
#         operand_one = create_register_operand(dst_register)
#         operand_two = create_register_operand(src_register)
#     elif mod == 0b00 and r_m == 0b110:  # direct address mode
#         effective_address_calculation: EffectiveAddressCalculation = get_effective_address_calculation_from_r_m_mod(r_m, mod)
#         dst_register: RegisterType = get_register_from_reg(reg, word_bit_set)
#         memory_address: int = byte_reader.read_next_two_byte_as_u16()
#
#         operand_one = create_register_operand(dst_register)
#         operand_two = create_effective_address_operand(effective_address_calculation, memory_address)
#     else:  # memory mode
#         displacement: Optional[int] = read_displacement_if_has_any(byte_reader, mod, r_m)
#         effective_address_calculation: EffectiveAddressCalculation = get_effective_address_calculation_from_r_m_mod(r_m, mod)
#         register: RegisterType = get_register_from_reg(reg, word_bit_set)
#         if dst_bit_set:  # memory to register
#             operand_one = create_register_operand(register)
#             operand_two = create_effective_address_operand(effective_address_calculation, displacement)
#         else:  # register to memory
#             operand_one = create_effective_address_operand(effective_address_calculation, displacement)
#             operand_two = create_register_operand(register)
#     return operand_one, operand_two


def contains_mov_opcode(opcode: int) -> bool:
    opcode_four: int = get_bits_from_byte(opcode, 0, 4, BitIndexDirection.FROM_LEFT)
    opcode_six: int = get_bits_from_byte(opcode, 0, 6, BitIndexDirection.FROM_LEFT)
    opcode_seven: int = get_bits_from_byte(opcode, 0, 7, BitIndexDirection.FROM_LEFT)

    return opcode_four == 0b1011 or opcode_seven == 0b1010000 or opcode_seven == 0b1010001 or opcode_seven == 0b1100011 or opcode_six == 0b100010 \
            or opcode == 0b10001110 or opcode == 0b10001100


def handle_mov_instruction(byte_reader: ByteReader) -> Operation:
    current_byte: int = byte_reader.read_next_byte_as_u8()
    assert contains_mov_opcode(current_byte), 'Opcode does not encode a mov'

    opcode_eight: int = current_byte
    opcode_four: int = get_bits_from_byte(current_byte, 0, 4, BitIndexDirection.FROM_LEFT)
    opcode_seven: int = get_bits_from_byte(current_byte, 0, 7, BitIndexDirection.FROM_LEFT)

    operation: Operation = Operation()
    operation.instruction_type = InstructionType.MOV

    if opcode_four == 0b1011:  # move immediate to register
        word_bit_set: bool = is_bit_set(current_byte, 3, BitIndexDirection.FROM_RIGHT)
        reg: int = get_bits_from_byte(current_byte, 2, 3, BitIndexDirection.FROM_RIGHT)
        immediate_value: int = byte_reader.read_one_or_two_bytes_as_u8_or_u16(word_bit_set)
        dst_register: RegisterMnemonic = get_register_from_reg(reg, word_bit_set)

        operation.operand_one = create_register_operand(dst_register)
        operation.operand_two = create_literal_value_operand(immediate_value, word_bit_set)
    elif opcode_seven == 0b1010000 or opcode_seven == 0b1010001:  # mov memory/accumulator to accumulator/memory
        word_bit_set: bool = is_bit_set(current_byte, 0, BitIndexDirection.FROM_RIGHT)
        memory_address: int = byte_reader.read_one_or_two_bytes_as_u8_or_u16(word_bit_set)
        effective_address_calculation: EffectiveAddressCalculation = EffectiveAddressCalculation.direct_address
        encodes_memory_to_register: bool = opcode_seven == 0b1010000

        if encodes_memory_to_register:
            operation.operand_one = create_register_operand(RegisterMnemonic.AX)
            operation.operand_two = create_effective_address_operand(effective_address_calculation, memory_address)
        else:
            operation.operand_one = create_effective_address_operand(effective_address_calculation, memory_address)
            operation.operand_two = create_register_operand(RegisterMnemonic.AX)
    elif opcode_seven == 0b1100011:  # mov immediate to register/memory
        operation.operand_one, operation.operand_two = handle_operands_for_imm_to_reg_mem(byte_reader, False)
    else:  # opcode_six in [0b100010, 0b10001110, 0b10001100] :  # mov register/memory to/from register
        operation.operand_one, operation.operand_two = handle_operands_for_reg_mem_to_from_reg_mem(byte_reader)
    return operation


def contains_add_sub_cmp_opcode(opcode: int) -> bool:
    opcode_six: int = get_bits_from_byte(opcode, 0, 6, BitIndexDirection.FROM_LEFT)
    opcode_seven: int = get_bits_from_byte(opcode, 0, 7, BitIndexDirection.FROM_LEFT)

    return opcode_six in [0b100000, 0b000000, 0b001010, 0b001110] or opcode_seven in [0b0000010, 0b0010110, 0b0011110]


def handle_add_sub_cmp_instruction(byte_reader: ByteReader) -> Operation:
    current_byte: int = byte_reader.read_next_byte_as_u8()
    assert contains_add_sub_cmp_opcode(current_byte), 'Opcode does not encode a add'

    opcode_six: int = get_bits_from_byte(current_byte, 0, 6, BitIndexDirection.FROM_LEFT)
    opcode_seven: int = get_bits_from_byte(current_byte, 0, 7, BitIndexDirection.FROM_LEFT)

    operation: Operation = Operation()

    if opcode_six == 0b000000 or opcode_seven == 0b0000010:
        operation.instruction_type = InstructionType.ADD
    elif opcode_six == 0b001010 or opcode_seven == 0b0010110:
        operation.instruction_type = InstructionType.SUB
    elif opcode_six == 0b001110 or opcode_seven == 0b0011110:
        operation.instruction_type = InstructionType.CMP
    else:
        reg: int = get_bits_from_byte(byte_reader.peek_as_u8(), 2, 3, BitIndexDirection.FROM_LEFT)
        if reg == 0b000:
            operation.instruction_type = InstructionType.ADD
        elif reg == 0b101:
            operation.instruction_type = InstructionType.SUB
        else:
            assert reg == 0b111, f'Invalid reg value {reg}'
            operation.instruction_type = InstructionType.CMP

    if opcode_six in [0b000000, 0b001010, 0b001110]:  # reg/mem to from reg/mem
        operation.operand_one, operation.operand_two = handle_operands_for_reg_mem_to_from_reg_mem(byte_reader)
    elif opcode_six == 0b100000:  # imm to mem/reg
        operation.operand_one, operation.operand_two = handle_operands_for_imm_to_reg_mem(byte_reader, True)
    else:  # opcode_seven == 0b00PPP10  # immediate to accumulator
        word_bit_set: bool = is_bit_set(current_byte, 0, BitIndexDirection.FROM_RIGHT)
        register_to_use: RegisterMnemonic = RegisterMnemonic.AX if word_bit_set else RegisterMnemonic.AL
        operation.operand_one = create_register_operand(register_to_use)
        immediate_value: int = byte_reader.read_one_or_two_bytes_as_u8_or_u16(word_bit_set)
        operation.operand_two = create_literal_value_operand(immediate_value, word_bit_set)

    return operation


def contains_jmp_opcode(opcode: int):
    return opcode in opcodes_for_jmp_instruction


def handle_jmp_instruction(byte_reader: ByteReader) -> Operation:
    current_byte: int = byte_reader.read_next_byte_as_u8()
    assert contains_jmp_opcode(current_byte), 'Opcode does not encode a jmp'

    operation: Operation = Operation()
    operation.instruction_type = opcodes_to_jmp_instructions_map[current_byte]

    current_byte = byte_reader.read_next_byte_as_s8()
    operation.operand_one = create_literal_value_offset_operand(current_byte)

    return operation


def main():
    file_name: str = sys.argv[1]
    output_file_name: str = f'{file_name}_my.asm'

    operations: list[Operation]
    with open(file_name, 'rb') as file:
        file_bytes = file.read()
        byte_reader: ByteReader = ByteReader(file_bytes)
        operations = decode(byte_reader)

    output: StringIO = StringIO()
    output.write('bits 16\n')
    output.write('\n'.join([str(operation) for operation in operations]))
    output.write('\n')

    output.seek(0)
    with open(output_file_name, 'w') as file:
        file.write(output.getvalue())


if __name__ == "__main__":
    main()
