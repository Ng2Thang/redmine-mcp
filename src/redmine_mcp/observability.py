import logging


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level.upper(), format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    for name in ("httpx", "httpcore", "fastapi_mcp"):
        logging.getLogger(name).setLevel(logging.WARNING)
