# src/core/logging.py
import sys
import structlog

def configure_logging():
    """Configure structlog for JSON output in production, console in dev."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            # Render as JSON in production, console in dev
            structlog.processors.JSONRenderer() #for machines
            if not sys.stdout.isatty() # Is this output going to a real human terminal? e.g laptop
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(structlog.stdlib.LOG_LEVELS["info"]),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Call this early in app startup
configure_logging()

# Export a logger instance for modules to use
logger = structlog.get_logger()