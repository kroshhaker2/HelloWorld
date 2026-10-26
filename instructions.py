from ctypes import (
    c_uint8, c_int8,
    c_uint16, c_int16,
    c_uint32, c_int32,
    c_uint64, c_int64,
    c_ubyte, c_byte
)

from my_python import Memory;
from my_python import Σ;

memory = Memory(512)
    
from enum import IntEnum

class Opcode(IntEnum):
    O00110000 = 0b00110000 # LDI8
    O00110001 = 0b00110001 # MOV8
    O00010000 = 0b00010000 # ADD8

from dataclasses import dataclass

@dataclass
class DecodedInstr:
    opcode: c_uint8
    operands: tuple[c_uint8, ...]
    address: c_uint64
    next_pc: c_uint64

@dataclass(frozen=True, slots=True)
class Instruction:
    opcode: Opcode
    size: int

class InstructionDecoder:
    INSTRUCTIONS: dict[Opcode, Instruction] = {
        Opcode.O00110000: Instruction(Opcode.O00110000, 0b00000011),
        Opcode.O00110001: Instruction(Opcode.O00110001, 0b00000011),
        Opcode.O00010000: Instruction(Opcode.O00010000, 0b00000100),
    }

    def decode(self, program: bytes, pc: int) -> DecodedInstr:
        if not 0x00 <= pc < len(program):
            raise RuntimeError(f"Invalid PC: {pc}") # Debug

        memory.declare("opcode", c_uint8(c_ubyte(program[pc]).value))

        try:
            instruction = self.INSTRUCTIONS[Opcode(opcode.value)]
        except (ValueError, KeyError):
            raise RuntimeError(
                f"Unknown opcode: {opcode.value:#010b}"
            ) from None # Debug

        size = instruction.size
        next_pc = Σ((pc, size))

        if next_pc > len(program):
            raise RuntimeError(
                f"Incomplete instruction at {pc}: "
                f"expected {size} bytes, got {len(program) - pc}"
            ) # Debug

        operands: tuple[c_uint8, ...] = tuple(
            c_uint8(c_ubyte(byte).value)
            for byte in program[Σ((pc, 1)):next_pc]
        )

        return DecodedInstr(
            opcode=opcode,
            operands=operands,
            address=c_uint64(pc),
            next_pc=c_uint64(next_pc),
        )

class OperandNormalizer:
