"""Capture the configured application console and restore process-wide logging state."""

import io
import logging
from collections.abc import Iterator
from copy import copy

import pytest

from redmine_mcp.observability import call_id, request_id


class Console(logging.StreamHandler):
    def __init__(self) -> None:
        self.output = io.StringIO()
        super().__init__(self.output)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.records.append(copy(record))

    def clear(self) -> None:
        self.records.clear()
        self.output.seek(0)
        self.output.truncate()


@pytest.fixture
def console() -> Iterator[Console]:
    root = logging.getLogger()
    loggers = [
        root,
        *(v for v in root.manager.loggerDict.values() if isinstance(v, logging.Logger)),
    ]
    states = [(v, v.level, v.disabled, v.propagate, v.handlers[:], v.filters[:]) for v in loggers]
    handlers = {
        h: (h.level, h.formatter, h.filters[:]) for logger in loggers for h in logger.handlers
    }
    request_token = request_id.set("-")
    call_token = call_id.set("-")
    capture = Console()
    root.handlers = [capture]
    try:
        yield capture
    finally:
        for value in tuple(root.manager.loggerDict.values()):
            if isinstance(value, logging.Logger) and value not in loggers:
                value.setLevel(logging.NOTSET)
                value.disabled = False
                value.propagate = True
                value.handlers = []
                value.filters = []
        for logger, level, disabled, propagate, saved_handlers, filters in states:
            logger.setLevel(level)
            logger.disabled = disabled
            logger.propagate = propagate
            logger.handlers = saved_handlers
            logger.filters = filters
        for handler, (level, formatter, filters) in handlers.items():
            handler.setLevel(level)
            handler.setFormatter(formatter)
            handler.filters = filters
        call_id.reset(call_token)
        request_id.reset(request_token)
        capture.close()
