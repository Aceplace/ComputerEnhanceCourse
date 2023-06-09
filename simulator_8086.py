from typing import Optional

from bit_manipulation_helpers import int_as_u16_hex_str
from decoder_8086 import decode, Operation, InstructionType, RegisterMnemonic, OperandType
import enum
import sys

from byte_reader import ByteReader


class RegisterType(enum.Enum):
    NONE = 0
    A = enum.auto()
    B = enum.auto()
    C = enum.auto()
    D = enum.auto()
    SP = enum.auto()
    BP = enum.auto()
    SI = enum.auto()
    DI = enum.auto()
    CS = enum.auto()
    DS = enum.auto()
    SS = enum.auto()
    ES = enum.auto()

    def can_do_hi_and_lo_byte(self) -> bool:
        return self in [RegisterType.A, RegisterType.B, RegisterType.C, RegisterType.D]


register_mnemonic_to_register_type_map: dict[RegisterMnemonic, RegisterType] = {
    RegisterMnemonic.AL: RegisterType.A,
    RegisterMnemonic.AH: RegisterType.A,
    RegisterMnemonic.AX: RegisterType.A,
    RegisterMnemonic.BL: RegisterType.B,
    RegisterMnemonic.BH: RegisterType.B,
    RegisterMnemonic.BX: RegisterType.B,
    RegisterMnemonic.CL: RegisterType.C,
    RegisterMnemonic.CH: RegisterType.C,
    RegisterMnemonic.CX: RegisterType.C,
    RegisterMnemonic.DL: RegisterType.D,
    RegisterMnemonic.DH: RegisterType.D,
    RegisterMnemonic.DX: RegisterType.D,
    RegisterMnemonic.SP: RegisterType.SP,
    RegisterMnemonic.BP: RegisterType.BP,
    RegisterMnemonic.SI: RegisterType.SI,
    RegisterMnemonic.DI: RegisterType.DI,
    RegisterMnemonic.CS: RegisterType.CS,
    RegisterMnemonic.DS: RegisterType.DS,
    RegisterMnemonic.SS: RegisterType.SS,
    RegisterMnemonic.ES: RegisterType.ES,
}


class RegisterPart(enum.Enum):
    NONE = 0
    LO = enum.auto()
    HI = enum.auto()
    FULL = enum.auto()

    def is_half(self):
        return self in [RegisterPart.HI, RegisterPart.LO]


def get_register_part_from_mnemonic(register_mnemonic: RegisterMnemonic):
    register_name: str = register_mnemonic.name
    if register_name[1] == 'L':
        return RegisterPart.LO
    elif register_name[1] == 'H':
        return RegisterPart.HI
    return RegisterPart.FULL


class Register:
    def __init__(self, register_type: RegisterType):
        self.register_type: RegisterType = register_type
        self.value: int = 0

    def __str__(self):
        name: str = self.register_type.name if not self.register_type.can_do_hi_and_lo_byte() else f'{self.register_type.name}X'
        hex_str: str = int_as_u16_hex_str(self.value)
        return f'{name}:  {hex_str}  {self.value}'

    def get_value_in_part(self, register_part: RegisterPart) -> int:
        assert register_part is not None, 'Register part not set'
        if register_part == RegisterPart.FULL:
            return self.value
        elif register_part == RegisterPart.LO:
            return self.value & 0xff
        else:  # register_part == RegisterPart.HI:
            return (self.value >> 8) & 0xff

    def set_value_in_part(self, value: int, register_part: RegisterPart):
        assert register_part is not None, 'Register part not set'

        if register_part == RegisterPart.FULL:
            self.value = value
        elif register_part == RegisterPart.LO:
            high_byte: int = self.value & 0xff00
            lo_byte: int = value
            self.value = high_byte | lo_byte
        else:  # register_part == RegisterPart.HI:
            high_byte: int = value
            lo_byte: int = self.value & 0xff
            self.value = (high_byte << 8) | lo_byte


class ProcessorFlags(enum.Flag):
    NONE = 0
    ZERO = enum.auto()
    SIGN = enum.auto()


class Processor8086:
    def __init__(self):
        self.registers: list[Register] = [
            Register(RegisterType.A),
            Register(RegisterType.B),
            Register(RegisterType.C),
            Register(RegisterType.D),
            Register(RegisterType.SP),
            Register(RegisterType.BP),
            Register(RegisterType.SI),
            Register(RegisterType.DI),
            Register(RegisterType.ES),
            Register(RegisterType.SS),
            Register(RegisterType.DS),
            Register(RegisterType.CS),
        ]

        self.register_type_to_registers_map: dict[RegisterType, Register] = {
            RegisterType.A: self.registers[0],
            RegisterType.B: self.registers[1],
            RegisterType.C: self.registers[2],
            RegisterType.D: self.registers[3],
            RegisterType.SP: self.registers[4],
            RegisterType.BP: self.registers[5],
            RegisterType.SI: self.registers[6],
            RegisterType.DI: self.registers[7],
            RegisterType.ES: self.registers[8],
            RegisterType.SS: self.registers[9],
            RegisterType.DS: self.registers[10],
            RegisterType.CS: self.registers[11],
        }

        self.flags: ProcessorFlags = ProcessorFlags.NONE
        self.instruction_ptr = 0
        self.operation_stream: Optional[list[Operation]] = None
        self.operation_stream_index: int = 0

    def get_register_from_mnemonic(self, register_mnemonic: RegisterMnemonic):
        register_type: RegisterType = register_mnemonic_to_register_type_map[register_mnemonic]
        register: Register = self.register_type_to_registers_map[register_type]
        return register

    def simulate_operation(self):
        operation: Operation = self.operation_stream[self.operation_stream_index]
        self.instruction_ptr += operation.num_bytes
        self.operation_stream_index += 1

        if operation.instruction_type == InstructionType.MOV:
            assert operation.operand_one.operand_type in [OperandType.REGISTER, OperandType.EFFECTIVE_ADDRESS], 'Must move into a register or memory location'
            # assuming operand one is register
            operand_one_register_mnemonic: RegisterMnemonic = operation.operand_one.value
            dst_register: Register = self.get_register_from_mnemonic(operand_one_register_mnemonic)
            dst_register_part: RegisterPart = get_register_part_from_mnemonic(operand_one_register_mnemonic)

            if operation.operand_two.operand_type.is_immediate_value():
                immediate_value: int = operation.operand_two.value
                dst_register.set_value_in_part(immediate_value, dst_register_part)
            else:  # Assume it is another register
                operand_two_register_mnemonic: RegisterMnemonic = operation.operand_two.value
                src_register: Register = self.get_register_from_mnemonic(operand_two_register_mnemonic)
                src_register_part: RegisterPart = get_register_part_from_mnemonic(operand_two_register_mnemonic)
                value: int = src_register.get_value_in_part(src_register_part)
                dst_register.set_value_in_part(value, dst_register_part)
        elif operation.instruction_type in [InstructionType.ADD, InstructionType.SUB, InstructionType.CMP]:
            # assuming operand one is register
            operand_one_register_mnemonic: RegisterMnemonic = operation.operand_one.value
            dst_register: Register = self.get_register_from_mnemonic(operand_one_register_mnemonic)
            dst_register_part: RegisterPart = get_register_part_from_mnemonic(operand_one_register_mnemonic)
            operand_one_value: int = dst_register.get_value_in_part(dst_register_part)

            if operation.operand_two.operand_type.is_immediate_value():
                operand_two_value: int = operation.operand_two.value
            else:  # Assume it is another register
                operand_two_register_mnemonic: RegisterMnemonic = operation.operand_two.value
                src_register: Register = self.get_register_from_mnemonic(operand_two_register_mnemonic)
                src_register_part: RegisterPart = get_register_part_from_mnemonic(operand_two_register_mnemonic)
                operand_two_value: int = src_register.get_value_in_part(src_register_part)

            if operation.instruction_type == InstructionType.ADD:
                result: int = operand_one_value + operand_two_value
            else:
                result: int = operand_one_value - operand_two_value

            if result > 65535 or result < -32768:
                result &= 0xffff

            self.flags = ProcessorFlags.NONE
            if (result & 0b1000000000000000) > 0:
                self.flags |= ProcessorFlags.SIGN
            if result == 0:
                self.flags |= ProcessorFlags.ZERO

            if operation.instruction_type != InstructionType.CMP:
                dst_register.set_value_in_part(result, dst_register_part)
        elif operation.instruction_type.is_jmp():
            assert operation.instruction_type == InstructionType.JNE, 'Have not implemented other jmps yet'
            jmp_amount: int = operation.operand_one.value

            # assume its jmp not zero
            if not (self.flags & ProcessorFlags.ZERO):
                total_jmp_delta: int = 0
                if jmp_amount > 0:
                    while total_jmp_delta < jmp_amount:
                        next_byte_jmp_delta: int = self.operation_stream[self.operation_stream_index].num_bytes
                        total_jmp_delta += next_byte_jmp_delta
                        self.instruction_ptr += next_byte_jmp_delta
                        self.operation_stream_index += 1
                        assert total_jmp_delta <= jmp_amount and self.operation_stream_index < len(self.operation_stream), 'Over shot the target for jmp'
                elif jmp_amount < 0:
                    while total_jmp_delta < abs(jmp_amount):
                        previous_byte_jmp_delta: int = self.operation_stream[self.operation_stream_index - 1].num_bytes
                        total_jmp_delta += previous_byte_jmp_delta
                        self.instruction_ptr -= previous_byte_jmp_delta
                        self.operation_stream_index -= 1
                        assert total_jmp_delta <= abs(jmp_amount) and self.operation_stream_index > 0, 'Over shot the target for jmp'


    def simulate(self):
        while self.operation_stream_index < len(self.operation_stream):
            print(self.operation_stream[self.operation_stream_index])
            print(f'IP pre-op: {int_as_u16_hex_str(self.instruction_ptr)} {self.instruction_ptr}')
            self.simulate_operation()
            self.print_register_and_flag_state()
            print(f'IP post-op: {int_as_u16_hex_str(self.instruction_ptr)} {self.instruction_ptr}')
            print()

    def print_register_and_flag_state(self):
        print('Register State:')
        for register in self.registers:
            print(f'\t{register}')
        print(f'Flags: {"S" if self.flags & ProcessorFlags.SIGN else ""}{"Z" if self.flags & ProcessorFlags.ZERO else ""}')


def main():
    file_name: str = sys.argv[1]

    with open(file_name, 'rb') as file:
        file_bytes = file.read()
        byte_reader: ByteReader = ByteReader(file_bytes)
        operations: list[Operation] = decode(byte_reader)

    simulator: Processor8086 = Processor8086()
    simulator.print_register_and_flag_state()
    simulator.operation_stream = operations
    simulator.simulate()


if __name__ == '__main__':
    main()
