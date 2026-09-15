import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

DEPLOY = Path(__file__).parent.parent / "deploy"
SOCKET = "/var/run/docker.sock"
BROKER_NETWORK = "api-broker"


@pytest.fixture(scope="module")
def resolved(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """The compose file as the server's compose resolves it, with placeholders
    for the values the server's env file names."""
    if shutil.which("docker") is None:
        pytest.skip("the file is read as compose resolves it, which needs docker")
    where = tmp_path_factory.mktemp("deploy")
    shutil.copytree(DEPLOY, where, dirs_exist_ok=True)
    (where / ".env").write_text("ALGO_COACH_IMAGE=engine\nDOCKER_GID=988\n")
    done = subprocess.run(
        ["docker", "compose", "-f", str(where / "compose.yaml"), "config", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)


def test_only_the_broker_mounts_the_container_runtime_s_socket(resolved: dict[str, Any]):
    """An API holding the socket would turn its own compromise into a root
    shell on the server."""
    mounting = {
        name
        for name, service in resolved["services"].items()
        if any(volume.get("source") == SOCKET for volume in service.get("volumes", []))
    }

    assert mounting == {"broker"}


def test_only_the_api_and_the_broker_join_the_broker_s_network(resolved: dict[str, Any]):
    """The network guards the broker with no secret to rotate, so Caddy and
    Postgres cannot open a connection to it."""
    joined = {
        name
        for name, service in resolved["services"].items()
        if BROKER_NETWORK in service.get("networks", {})
    }

    assert joined == {"api", "broker"}


def test_the_broker_joins_no_other_network(resolved: dict[str, Any]):
    """On the default network, Caddy and Postgres would reach it after all."""
    assert set(resolved["services"]["broker"]["networks"]) == {BROKER_NETWORK}


def test_the_broker_s_network_leads_nowhere_outside(resolved: dict[str, Any]):
    """The broker reaches Docker through the socket and pulls nothing, so a
    route out would serve only an attacker holding the broker."""
    assert resolved["networks"][BROKER_NETWORK]["internal"] is True
