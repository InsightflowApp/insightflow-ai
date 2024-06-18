from pathlib import Path
import os
import sys
from typing import Literal, Callable
import traceback

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
        time=None,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        if time is None:
            time = datetime.now()
        with open(self._log_folder / "info.log", "a") as f:
            print(f"{time} INFO - ", file=f, end="")
            print(*content, sep=sep, end=end, file=f, flush=flush)

        # also print to stdout
        print(*content, sep=sep, end=end, flush=flush)
        self.debug(*content, time=time, sep=sep, end=end, flush=flush)

    def debug(
        self,
        *content,
        time=None,
        objects: dict | None = None,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        if time is None:
            time = datetime.now()
        with open(self._log_folder / "debug.log", "a") as f:
            print(f"{time} DEBUG - ", file=f, end="")
            print(*content, sep=sep, end=end, file=f, flush=flush)

    def error(
        self,
        *content,
        exception: type[BaseException] | None = None,
        time=None,
        sep: str | None = " ",
        end: str | None = "\n",
        flush: Literal[False] = False,
    ):
        if time is None:
            time = datetime.now()
        with open(self._log_folder / "error.log", "a") as f:
            print(f"{time} ERROR - ", file=f, end="")
            print(*content, exception, sep=sep, end=end, file=f, flush=flush)
            # traceback.print_exception(file=f)
            traceback.print_exc(sys.exc_info())
            # traceback.print_tb(tb=exception, file=f)

        print(*content, f"\n\033[91m{exception}\033[0m\n")
        self.debug(f"Error:", *content, time=time, sep=sep, end=end, flush=flush)

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
