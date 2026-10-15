"""SET-01/02: exact release/profile selection without import-time side effects."""

import sys

import pytest

from tests.e2e_setup_helpers import SetupSandbox
from tests.e2e_setup_helpers import setup_sandbox as setup_sandbox


@pytest.mark.parametrize("version,port", [("6.0.1", 3001), ("7.0.2", 3002)])
def test_builtin_identity_paths_commands_and_environment(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, version: str, port: int
) -> None:
    monkeypatch.setenv("REDMINE_E2E_VERSION", version)
    monkeypatch.setenv("REDMINE_TEST_VERSION", "unrelated-terminal-version")
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    project = f"redmine-mcp-dev-{version.replace('.', '-')}"
    assert module.PROJECT == project and module.VERSION == version
    assert module.URL == f"http://127.0.0.1:{port}"
    assert module.COMPOSE_FILE == setup_sandbox.root / "deploy" / f"compose.test.{version}.yaml"
    assert module.ENV_FILE is None
    assert module.STATE == setup_sandbox.root / ".local/e2e" / project
    assert module.compose_command("up", "postgres", "redmine") == [
        sys.executable,
        str(setup_sandbox.root / "scripts/local_env.py"),
        "compose",
        "-f",
        str(setup_sandbox.root / "deploy/compose.e2e.yaml"),
        "up",
        "postgres",
        "redmine",
    ]
    environment = module.process_environment()
    assert environment["REDMINE_TEST_VERSION"] == version
    assert environment["REDMINE_E2E_VERSION"] == version
    assert environment["REDMINE_E2E_STATE"] == module.STATE.as_posix()
    assert environment["MSYS_NO_PATHCONV"] == "1"
    assert environment["MSYS2_ARG_CONV_EXCL"] == "*"
    assert not module.STATE.exists()


def test_default_release_is_seven(setup_sandbox: SetupSandbox) -> None:
    assert setup_sandbox.load("tools/testing/e2e_config.py").VERSION == "7.0.2"


@pytest.mark.parametrize(
    "version",
    [
        "latest",
        "6",
        "6.0",
        "06.0.1",
        "6.01.1",
        "6.0.01",
        "6.0.1-rc1",
        "5.1.0",
        "7.0.1",
        "7.0.3",
        "8.0.0",
        " 7.0.2",
        "7.0.2\n",
    ],
)
def test_unsupported_versions_fail_on_import(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    monkeypatch.setenv("REDMINE_E2E_VERSION", version)
    with pytest.raises(ValueError, match="exact 6.x.x release or 7.0.2"):
        setup_sandbox.load("tools/testing/e2e_config.py")
    assert not (setup_sandbox.root / ".local").exists()


@pytest.mark.parametrize(
    "settings,message",
    [
        ({"REDMINE_E2E_VERSION": "6.1.2"}, "explicit REDMINE_E2E_COMPOSE_FILE"),
        ({"REDMINE_E2E_COMPOSE_PROJECT": "foreign"}, "complete custom Compose profile"),
        ({"REDMINE_E2E_ENV_FILE": ".env"}, "do not use an env file"),
        ({"REDMINE_E2E_COMPOSE_FILE": "deploy/custom.yaml"}, "requires COMPOSE_PROJECT"),
    ],
)
def test_incomplete_or_conflicting_profiles_fail(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    settings: dict[str, str],
    message: str,
) -> None:
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=message):
        setup_sandbox.load("tools/testing/e2e_config.py")


def custom_profile(sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch) -> None:
    (sandbox.root / "deploy/custom.yaml").write_text("# custom fixture\n")
    for name, value in {
        "REDMINE_E2E_VERSION": "6.1.2",
        "REDMINE_E2E_COMPOSE_FILE": "deploy/custom.yaml",
        "REDMINE_E2E_COMPOSE_PROJECT": "owned-custom",
        "REDMINE_E2E_ENV_FILE": ".local/custom.env",
        "REDMINE_E2E_PORT": "3100",
    }.items():
        monkeypatch.setenv(name, value)


def test_explicit_custom_release_never_falls_back(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom_profile(setup_sandbox, monkeypatch)
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    assert module.VERSION == "6.1.2" and module.PROJECT == "owned-custom"
    assert module.URL == "http://127.0.0.1:3100"
    assert module.STATE == setup_sandbox.root / ".local/e2e/6.1.2"
    assert module.compose_command("config") == [
        "docker",
        "compose",
        "-p",
        "owned-custom",
        "--env-file",
        str(setup_sandbox.root / ".local/custom.env"),
        "-f",
        str(setup_sandbox.root / "deploy/compose.yaml"),
        "-f",
        str(setup_sandbox.root / "deploy/custom.yaml"),
        "config",
    ]


@pytest.mark.parametrize(
    "missing",
    [
        "REDMINE_E2E_COMPOSE_PROJECT",
        "REDMINE_E2E_ENV_FILE",
        "REDMINE_E2E_PORT",
    ],
)
def test_each_custom_setting_is_required(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    custom_profile(setup_sandbox, monkeypatch)
    monkeypatch.delenv(missing)
    with pytest.raises(ValueError, match="requires COMPOSE_PROJECT"):
        setup_sandbox.load("tools/testing/e2e_config.py")


@pytest.mark.parametrize(
    "name,value,message",
    [
        ("REDMINE_E2E_COMPOSE_FILE", "../outside.yaml", "within the repository"),
        ("REDMINE_E2E_COMPOSE_FILE", "deploy/missing.yaml", "does not exist"),
        ("REDMINE_E2E_ENV_FILE", "../outside.env", "within the repository"),
        ("REDMINE_E2E_ENV_FILE", "deploy/credentials.env", "ignored .local"),
        ("REDMINE_E2E_COMPOSE_PROJECT", "Bad Project", "Invalid E2E Compose project"),
    ],
)
def test_custom_paths_and_project_refuse_invalid_targets(
    setup_sandbox: SetupSandbox,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
    message: str,
) -> None:
    custom_profile(setup_sandbox, monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match=message):
        setup_sandbox.load("tools/testing/e2e_config.py")


@pytest.mark.parametrize("port", ["0", "1023", "65536", "-1", "not-a-port"])
def test_invalid_ports_refused(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("REDMINE_E2E_PORT", port)
    with pytest.raises(ValueError):
        setup_sandbox.load("tools/testing/e2e_config.py")


@pytest.mark.parametrize("port", [1024, 65535])
def test_port_boundaries(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch, port: int
) -> None:
    monkeypatch.setenv("REDMINE_E2E_PORT", str(port))
    assert setup_sandbox.load("tools/testing/e2e_config.py").PORT == port


@pytest.mark.parametrize(
    "image",
    [
        "redmine:7.0.2",
        "redmine:latest@sha256:" + "a" * 64,
        "redmine:6.0.1@sha256:" + "a" * 64,
        "foreign/redmine:7.0.2@sha256:" + "a" * 64,
        "redmine:7.0.2@sha256:" + "a" * 63,
        "redmine:7.0.2@sha256:" + "G" * 64,
    ],
)
def test_image_pin_refusals(setup_sandbox: SetupSandbox, image: str) -> None:
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    with pytest.raises(ValueError, match="selected-version"):
        module.validate_image(image)


def test_image_override_must_match_selected_digest(
    setup_sandbox: SetupSandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    image = "redmine:7.0.2-bookworm@sha256:" + "a" * 64
    assert module.validate_image(image) == image
    monkeypatch.setenv("REDMINE_E2E_IMAGE", image.replace("a" * 64, "b" * 64))
    with pytest.raises(ValueError, match="match the selected Compose image pin"):
        module.validate_image(image)


@pytest.mark.parametrize("script", ["../seed.rb", "seed.rb;touch x", "/seed.rb", "seed.py"])
def test_native_command_rejects_script_injection(setup_sandbox: SetupSandbox, script: str) -> None:
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    with pytest.raises(ValueError, match="Invalid native"):
        module.native_command(script)


def test_native_command_preserves_container_path_and_arguments(
    setup_sandbox: SetupSandbox,
) -> None:
    module = setup_sandbox.load("tools/testing/e2e_config.py")
    assert module.native_command("e2e_seed.rb", "--owned")[-8:] == [
        "-T",
        "redmine",
        "bundle",
        "exec",
        "rails",
        "runner",
        "/opt/testing/e2e_seed.rb",
        "--owned",
    ]
    assert module.repository_path("deploy/../deploy") == setup_sandbox.root / "deploy"
