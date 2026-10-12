"""Shared configuration for owned live fixtures, selected before process startup."""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = os.environ.get("REDMINE_E2E_VERSION", "7.0.2")
if not re.fullmatch(r"6\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)|7\.0\.2", VERSION):
    raise ValueError("REDMINE_E2E_VERSION must be an exact 6.x.x release or 7.0.2")

# Keep the existing default environment and separate every other release's data.
SUFFIX = "" if VERSION == "7.0.2" else "-" + VERSION.replace(".", "-")
PROJECT = "redmine-mcp-e2e" + SUFFIX
CONTAINER = PROJECT + "-redmine-1"
STATE = ROOT / ".local" / ("testing-e2e" + SUFFIX)
PORT = int(os.environ.get("REDMINE_E2E_PORT", "3001" if VERSION == "7.0.2" else "3002"))
if not 1024 <= PORT <= 65535:
    raise ValueError("REDMINE_E2E_PORT must be between 1024 and 65535")
URL = f"http://127.0.0.1:{PORT}"


def validate_image(image: str) -> str:
    """Require an official, version-matching, immutable Redmine image reference."""
    pattern = rf"redmine:{re.escape(VERSION)}(?:-[a-z0-9.-]+)?@sha256:[0-9a-f]{{64}}"
    if not re.fullmatch(pattern, image):
        raise ValueError("E2E image must be redmine:<selected-version>[-variant]@sha256:<digest>")
    return image
