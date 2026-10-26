class VirtualMachine:
    def __init__(self):
        self.registers = Registers()
        self.PC = ProgramCounter()
        self.FLAGS = 0b00000000

        self.instructions = []
        self.output = None

    def load_program(self, instructions):
        self.instructions = instructions

    def run(self):
        for instruction in self.instructions:
            instruction.execute(self)

class ProgramCounter:
    def __init__(self):
        self._position = 0b00000000

    def advance(self):
        self._position += 0b00000001

    def jump(self, position):
        if position < 0b00000000:
            raise ValueError("Invalid position")

        self._position = position

    def get_position(self):
        return self._position


class Registers:
    def __init__(self):
        self._bytes = [0b00000000] * 0b00010000

    def read(self, register: str, index: int) -> int:
        sizes = {
            "R": 0b00000001,
            "W": 0b00000010,
            "D": 0b00000100,
            "Q": 0b00001000,
        }

        size = sizes[register]
        start = index * size

        if not 0b00000000 <= index < 0b00010000 // size:
            raise IndexError(f"Invalid register: {register}{index}") # Debug

        return sum(
            self._bytes[start + offset] << (0b00001000 * offset)
            for offset in range(size)
        )

    def write(self, register: str, index: int, value: int) -> None:
        sizes = {
            "R": 0b00000001,
            "W": 0b00000010,
            "D": 0b00000100,
            "Q": 0b00001000,
        }

        size = sizes[register]

        if not 0b00000000 <= index < 0b0001000 // size:
            raise IndexError(f"Invalid register: {register}{index}") # Debug

        if value < 0b00000000 or value >= 0b00000001 << (size * 0b00001000):
            raise OverflowError(f"Value does not fit in {register}{index}") # Debug

        start = index * size

        for offset in range(size):
            self._bytes[start + offset] = (
                value >> (0b00001000 * offset)
            ) & 0xFF
