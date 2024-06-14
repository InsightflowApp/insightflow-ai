from pathlib import Path
import os
from typing import Literal, Callable

"""write to debug, error, and info logs"""

from datetime import datetime


class Logger:
    def __init__(self, log_folder: os.PathLike = "server/logs"):
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        self._log_folder: Path = Path(log_folder)

    def info(
        self,
        *content,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        with open(self._log_folder / "info.log", "a") as f:
            print(f"{datetime.now()} INFO - ", file=f, end="")
            print(*content, sep=sep, end=end, file=f, flush=flush)

        # also print to stdout
        print(*content, sep=sep, end=end, flush=flush)

    def debug(
        self,
        *content,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        with open(self._log_folder / "debug.log", "a") as f:
            print(f"{datetime.now()} DEBUG - ", file=f, end="")
            print(*content, sep=sep, end=end, file=f, flush=flush)

    def error(
        self,
        *content,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        with open(self._log_folder / "error.log", "a") as f:
            print(f"{datetime.now()} ERROR - ", file=f, end="")
            print(*content, sep=sep, end=end, file=f, flush=flush)

    def clear(self, *to_clear):
        if len(to_clear) == 0:
            # clear all
            to_clear = ["info.log", "debug.log", "error.log"]
        for filename in to_clear:
            with open(self._log_folder / filename, "w") as f:
                print(f"{datetime.now()} INFO - Created log.", file=f)


logger = Logger()


if __name__ == "__main__":
    #   logger = Logger()
    logger.clear()
    logger.debug("successfully wrote to debug")
    logger.error("successfully wrote to error")
    logger.debug("wrote again to debug")
