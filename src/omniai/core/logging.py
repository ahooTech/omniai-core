# src/omniai/core/logging.py
import logging
import sys

import structlog
from structlog import get_logger


def configure_logging():
    # Set root logger level
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Detect dev vs prod
    is_dev = sys.stdout.isatty()

    # Processors shared by both structlog and stdlib
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if is_dev:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 🔥 CRITICAL: Route standard library logs through structlog
    structlog.stdlib.recreate_defaults()

configure_logging()
logger = get_logger()
