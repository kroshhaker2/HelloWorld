import subprocess

code = "\n".join(
    f"        elif opcode == 0x{i:02X}:\n"
    f"            self.__dispatch_{i}(opcode, state)"
    for i in range(256)
)

subprocess.run(["wl-copy"], input=code, text=True)