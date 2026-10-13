"""Decode Redmine's native rational hours without relaxing public input models."""

import re
from fractions import Fraction

from fastapi import status as http_status

from redmine_mcp.common import ApplicationError
from redmine_mcp.constants import codes as codes_text
from redmine_mcp.constants import redmine as redmine_text


def native_hours(value: object) -> object:
    """Redmine 6.0.1 serializes its whole-minute Rational getter as 'n/d'."""
    if not isinstance(value, str):
        return value
    if len(value) <= 128 and re.fullmatch(r"(0|[1-9][0-9]*)/[1-9][0-9]*", value):
        try:
            return float(Fraction(value))
        except (ValueError, OverflowError, ZeroDivisionError):
            pass
    raise ApplicationError(
        codes_text.UPSTREAM_RESPONSE,
        redmine_text.UNEXPECTED_DATA,
        http_status.HTTP_502_BAD_GATEWAY,
    )
