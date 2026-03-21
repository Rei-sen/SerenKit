from __future__ import annotations

import os
import sys


def _get_console_width() -> int:
    return os.get_terminal_size().columns


def _clear_line() -> None:
    print("\r" + " " * _get_console_width() + "\r", end="", flush=True)


def main() -> int:
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        line = line.rstrip("\n")

        if line == "DONE":
            _clear_line()
            break
        max_width = _get_console_width()

        if line.startswith("s:"):
            _clear_line()
            print(line[2:max_width], flush=True)
            continue

        if line.startswith("p:"):
            _clear_line()
            print(line[2:max_width], end="", flush=True)

    print()
    input("[Export complete, feel free to close this window]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
