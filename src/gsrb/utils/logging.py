import io
import logging
import sys
from functools import wraps
from typing import Callable, Generic, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")

log_in_memory = io.StringIO()


class ExecuteOnce(Generic[T]):
    def __init__(self) -> None:
        self.executed = False
        self.result: T | None = None

    def __call__(self, func: Callable[P, T | None]) -> Callable[P, T | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            if not self.executed:
                self.executed = True
                self.result = func(*args, **kwargs)
                return self.result
            else:
                return self.result

        return wrapper


@ExecuteOnce()
def config_logger() -> None:
    """配置日志"""
    # 根 logger
    logger = logging.getLogger("gsrb")
    formatter = logging.Formatter(
        "%(name)-30s %(lineno)-4d %(levelname)-8s %(message)s"
    )

    file_handler = logging.FileHandler("gsrb.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    debug_handler = logging.FileHandler("gsrb.debug.log", mode="w", encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    std_handler = logging.StreamHandler(sys.stdout)
    std_handler.setLevel(logging.INFO)
    std_handler.setFormatter(formatter)

    memory_handler = logging.StreamHandler(log_in_memory)
    memory_handler.setLevel(logging.DEBUG)
    memory_handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(std_handler)
    logger.addHandler(memory_handler)
