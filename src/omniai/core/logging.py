# src/omniai/core/logging.py
import logging
import sys
from typing import Any, Callable, Mapping, MutableMapping, Tuple, Union

import structlog
from structlog import get_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer

# Define the processor type to help MyPy
ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[Mapping[str, Any], str, bytes, bytearray, Tuple[Any, ...]]
]

def configure_logging() -> None:
    # Set root logger level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Detect dev vs prod
    is_dev = sys.stdout.isatty()

    # Shared processors
    shared_processors: list[ProcessorType] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Annotate renderer with union type
    renderer = ConsoleRenderer() if is_dev else JSONRenderer()

    # Final processor list
    all_processors: list[ProcessorType] = shared_processors + [renderer]

    structlog.configure(
        processors=all_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 🔥 CRITICAL: Route standard library logs through structlog
    structlog.stdlib.recreate_defaults()


configure_logging()
logger = get_logger()
