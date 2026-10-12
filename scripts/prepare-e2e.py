"""Prepare E2E fixtures in the selected existing versioned Compose stack."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.testing.e2e_config import (  # noqa: E402
    PROJECT,
    STATE,
    URL,
    VERSION,
    compose_command,
    native_command,
)
from tools.testing.e2e_environment import (  # noqa: E402
    compose_configuration,
    initialize_credentials,
    manifest,
    preflight,
    reset_stack,
    run,
    validate_existing_containers,
    validate_running,
    validate_volumes,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Discard only the selected marked stack's database/files and E2E state before setup",
    )
    arguments = parser.parse_args()
    try:
        initialize_credentials()
        configuration = compose_configuration()
        validate_volumes(reset=arguments.reset)
        validate_existing_containers(reset=arguments.reset)
        if arguments.reset:
            reset_stack()
        elif (STATE / "fixtures.json").exists():
            manifest()
        STATE.mkdir(parents=True, exist_ok=True)
        result = run(
            compose_command("up", "-d", "--wait", "--wait-timeout", "600", "postgres", "redmine")
        )
        (STATE / "compose-up.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode:
            raise ValueError(
                f"Cannot start selected stack {PROJECT} at {URL}; inspect private compose-up.log"
            )
        validate_running(configuration)
        seeded = run(native_command("e2e_seed.rb"))
        (STATE / "seed.log").write_text(seeded.stdout + seeded.stderr, encoding="utf-8")
        if seeded.returncode:
            raise ValueError("E2E fixture seed failed; inspect private seed.log before retrying")
        preflight()
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Never include Docker config, env values, credentials, or raw subprocess output.
        message = "E2E configuration or tooling failure"
        if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError):
            message = str(error)
        raise SystemExit(message) from None
    print(f"E2E ready: Redmine {VERSION} | {PROJECT} | {URL}")
    print(f"Private fixture state: {STATE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
