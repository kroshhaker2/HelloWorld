"""Мой код - мои правила"""

from typing import cast

#region OPERATIONS

from builtins import sum as Σ


#endregion

#region TYPES

class Type:
    SIZE: int
    SIGNED: bool = False

    @classmethod
    def encode(cls, value: int) -> bytes:
        return value.to_bytes(cls.SIZE, "little", signed=cls.SIGNED)

class UInt8(Type, int):
    SIZE = 0x01

    def __new__(cls, value: int):
        if not 0 <= value <= 0xFF:
            raise ValueError("UInt8 out of range")
        return super().__new__(cls, value)

class UInt16(Type, int):
    SIZE = 0x02

    def __new__(cls, value: int):
        if not 0 <= value <= 0xFFFF:
            raise ValueError("UInt16 out of range")
        return super().__new__(cls, value)

class UInt32(Type, int):
    SIZE = 0x04

    def __new__(cls, value: int):
        if not 0 <= value <= 0xFFFFFFFF:
            raise ValueError("UInt32 out of range")
        return super().__new__(cls, value)

class UInt64(Type, int):
    SIZE = 0x08

    def __new__(cls, value: int):
        if not 0 <= value <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("UInt64 out of range")
        return super().__new__(cls, value)


class Int8(Type, int):
    SIZE = 0x01
    SIGNED = True

    def __new__(cls, value: int):
        if not -0x80 <= value <= 0x7F:
            raise ValueError("Int8 out of range")
        return super().__new__(cls, value)

class Int16(Type, int):
    SIZE = 0x02
    SIGNED = True

    def __new__(cls, value: int):
        if not -0x8000 <= value <= 0x7FFF:
            raise ValueError("Int16 out of range")
        return super().__new__(cls, value)

class Int32(Type, int):
    SIZE = 0x04
    SIGNED = True
    
    def __new__(cls, value: int):
        if not -0x80000000 <= value <= 0x7FFFFFFF:
            raise ValueError("Int32 out of range")
        return super().__new__(cls, value)

class Int64(Type, int):
    SIZE = 0x08
    SIGNED = True
    
    def __new__(cls, value: int):
        if not -0x8000000000000000 <= value <= 0x7FFFFFFFFFFFFFFF:
            raise ValueError("Int64 out of range")
        return super().__new__(cls, value)


class Bool(Type, int):
    SIZE = 0x01

    def __new__(cls, value: int):
        if value not in (0x00, 0x01):
            raise ValueError("Bool out of range")
        return super().__new__(cls, value)

#endregion

#region MEMORY

"""Память.
Философия этой идеи:
  Ручное управление памятью. Можно забыть выделить память,
повторно использовать адрес или выйти за границы.
  При ошибке сообщается адрес и код причины, а дальше сам.
"""


class RuntimeMemory:
    """Управление памятью времени выполнения.

    Объявите, выделите, присвойте, прочитайте и уберитесь…
    Здесь все переменные глобальные. Думайте, что пишете.
    """

    def __init__(self, size):
        """Инициализация памяти.\n
        Args:\n
            size: размер памяти в байтах
        """

        self._size = size
        self._memory_buffer = bytearray(size)
        self._variables: dict[str, tuple[UInt64, type[Type]]] = {}
        self._used: int = 0x00
        self._free_blocks: list[tuple[int, int]] = [
            (0x00, self._size)
        ]

    def _find_free_block(self, type_size: int) -> int:
        for i, (address, size) in enumerate(self._free_blocks):
            if size >= type_size:
                return i

        raise MemoryError("Not enough memory")
    
    @property
    def size(self) -> UInt64:
        """Размер выделенной памяти в байтах
        """
        return UInt64(self._size)

    @property
    def used(self) -> UInt64:
        """Количество занятых байт
        """
        return UInt64(self._used)

    def declare(self, name: str, data_type: type[Type]) -> None:
        """Декларация переменной.\n
        Не выделяет место под неё.

        Args:\n
            name: имя переменной (str)\n
            data_type: тип переменной (type)
        """

        if not issubclass(data_type, Type):
            raise TypeError("Invalid data type") # Debug

        if self._variables.get(name) != None:
            raise NameError(f"Variable already exists: {name}") # Debug

        self._variables[name] = (UInt64(self._size), data_type)

    def allocate(self, name: str) -> None:
        """Выделить участок памяти под переменную.\n

        Args:\n
            name: имя переменной (str)\n
        """

        if self._variables.get(name) is None:
            raise NameError(f"Variable does not exist: {name}") # Debug

        data_type: type[Type] = self._variables[name][1]
        index_free_block: int = self._find_free_block(data_type.SIZE)

        address, block_size = self._free_blocks[index_free_block]

        self._variables[name] = (UInt64(address), data_type)

        if block_size == data_type.SIZE:
            self._free_blocks.pop(index_free_block)
        else:
            self._free_blocks[index_free_block] = (
                address + data_type.SIZE,
                block_size - data_type.SIZE,
            )
        
    def assign(self, name: str, value: object) -> None:
        """Задать значение переменной.\n

        Args:\n
            name: имя переменной (str)\n
            value: значение переменной (object)\n
        """

        if self._variables.get(name) is None:
            raise NameError(f"Variable does not exist: {name}") # Debug

        address, data_type = self._variables[name]

        if value is None or not isinstance(value, data_type):
            raise TypeError(f"Invalid type for {name}") # Debug

        self._memory_buffer[address:address + data_type.SIZE] = data_type.encode(cast(int, value))
    
    def free(self, name: str) -> None:
        """Освободить выделенный участок переменной\n

        Args:\n
            name: имя переменной (str)\n
        """

        if self._variables.get(name) is None:
            raise NameError(f"Variable does not exist: {name}") # Debug

        address, data_type = self._variables[name]

        self._memory_buffer[address:address + data_type.SIZE] = bytes(data_type.SIZE)

        self._variables[name] = (UInt64(self._size), data_type)

        self._free_blocks.append((address, data_type.SIZE))
        self._free_blocks.sort()

        merged: list[tuple[int, int]] = []

        for current_address, current_size in self._free_blocks:
            if merged:
                last_address, last_size = merged[-1]

                if last_address + last_size == current_address:
                    merged[-1] = (
                        last_address,
                        last_size + current_size,
                    )
                    continue

            merged.append((current_address, current_size))

        self._free_blocks = merged

    def release(self, name: str) -> None:
        """Удалить запись переменной\n

        Args:\n
            name: имя переменной (str)\n
        """

        if self._variables.get(name) is None:
            raise NameError(f"Variable does not exist: {name}") # Debug

        del self._variables[name]

#endregion

#region CONDITIONAL STATEMENTS

class Condition:
    def __init__(self, condition: bool):
        self.condition = condition

    def THEN(self, action):
        if self.condition:
            action()
        return self

    def ELSE(self, action):
        if not self.condition:
            action()
        return self


def IF(condition: bool) -> Condition:
    return Condition(condition)

#endregion