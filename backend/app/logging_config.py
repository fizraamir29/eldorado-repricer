"""
Logging setup. Uses plain readable format for local dev, and can be switched
to JSON-style structured logs in production by setting LOG_JSON=true in .env
(useful if you pipe logs into a service that parses JSON).
"""
import logging
import os
import sys

_JSON_FORMAT = (
    '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
)
_PLAIN_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging():
    use_json = os.getenv("LOG_JSON", "false").lower() == "true"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_JSON_FORMAT if use_json else _PLAIN_FORMAT))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    # Quiet down noisy third-party loggers.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
