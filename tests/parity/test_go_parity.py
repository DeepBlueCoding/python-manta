import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Module-level marker: golang tests requiring Go toolchain (~1min)
pytestmark = pytest.mark.golang

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from caching_parser import Parser

GO_WRAPPER_DIR = ROOT_DIR / "go_wrapper"
DEFAULT_CALLBACKS = (
    ("CDemoFileHeader", 1),
    ("CDOTAUserMsg_ChatMessage", 5),
    ("CDOTAUserMsg_LocationPing", 5),
    ("CNETMsg_Tick", 10),
    ("CSVCMsg_ServerInfo", 1),
)


def _iter_candidate_replays():
    env_file = os.getenv("PYTHON_MANTA_REPLAY")
    if env_file:
        yield Path(env_file)
    env_dir = os.getenv("PYTHON_MANTA_REPLAY_DIR")
    if env_dir:
        yield from _iter_directory(Path(env_dir))
    yield from _iter_directory(ROOT_DIR / "tests" / "fixtures" / "replays")
    yield from _iter_directory(Path.home() / "dota2" / "replays")


def _iter_directory(directory: Path):
    if directory.is_file():
        yield directory
        return
    if not directory.exists():
        return
    for path in sorted(directory.glob("*.dem")):
        if path.is_file():
            yield path


@pytest.fixture(scope="session")
def replay_path():
    for candidate in _iter_candidate_replays():
        if candidate.exists() and candidate.is_file():
            return candidate
    pytest.skip(
        "No replay file found. Set PYTHON_MANTA_REPLAY or copy a .dem file into tests/fixtures/replays/."
    )


@pytest.fixture(scope="session")
def go_binary():
    go = shutil.which("go")
    if not go:
        pytest.skip("Go toolchain not available in PATH")
    return go


@pytest.fixture(scope="session")
def ensure_manta_repo(go_binary):  # noqa: ARG001
    manta_dir = GO_WRAPPER_DIR / "manta"
    if manta_dir.exists():
        return manta_dir
    prepare_script = ROOT_DIR / "tools" / "prepare_manta.sh"
    if not prepare_script.exists():
        pytest.skip("prepare_manta.sh is missing; cannot fetch manta dependency")
    try:
        subprocess.run(
            ["bash", str(prepare_script)],
            cwd=ROOT_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        pytest.skip(f"Failed to prepare manta dependency: {exc.stderr.decode().strip() or exc}")
    if not manta_dir.exists():
        pytest.skip("Manta repository unavailable after preparation step")
    return manta_dir


@pytest.fixture(scope="session")
def manta_parser(replay_path):  # noqa: ARG001
    library_path = os.getenv("PYTHON_MANTA_LIBRARY_PATH")
    if library_path:
        candidate = Path(library_path)
    else:
        candidate = ROOT_DIR / "src" / "python_manta" / "libmanta_wrapper.so"
    if not candidate.exists():
        pytest.skip(
            "Shared library libmanta_wrapper.so not found. Run ./build.sh or tools/before_build_linux.sh first."
        )
    return Parser(str(replay_path), library_path=str(candidate))


@pytest.fixture()
def go_parity_runner(go_binary, ensure_manta_repo):  # noqa: ARG001
    def runner(callback: str, limit: int, replay: Path):
        cmd = [
            go_binary,
            "run",
            "./cmd/parity",
            "--replay",
            str(replay),
            "--callbacks",
            callback,
            "--limit",
            str(limit),
        ]
        result = subprocess.run(
            cmd,
            cwd=GO_WRAPPER_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(
                "go parity command failed: "
                f"{result.stderr.strip() or result.stdout.strip() or 'unknown error'}"
            )
        payload = json.loads(result.stdout)
        callbacks = payload.get("callbacks", {})
        if callback not in callbacks:
            pytest.fail(f"Callback {callback} missing from Go parity output")
        return callbacks[callback]

    return runner


def _canonicalize(data):
    return json.loads(json.dumps(data, sort_keys=True, separators=(",", ":")))


@pytest.mark.integration
@pytest.mark.parametrize("callback,limit", DEFAULT_CALLBACKS)
def test_python_matches_go(callback, limit, replay_path, manta_parser, go_parity_runner):
    go_result = go_parity_runner(callback, limit, replay_path)
    assert go_result.get("success", False), go_result.get("error")

    python_result = manta_parser.parse(
        messages={"filter": callback, "max_messages": limit}
    )
    assert python_result.success, python_result.error

    python_messages = [
        {
            "type": message.type,
            "tick": message.tick,
            "net_tick": message.net_tick,
            "data": _canonicalize(message.data),
        }
        for message in python_result.messages.messages
    ]

    go_messages = [
        {
            "type": msg.get("type"),
            "tick": msg.get("tick"),
            "net_tick": msg.get("net_tick"),
            "data": _canonicalize(msg.get("data")),
        }
        for msg in go_result.get("messages", [])
    ]

    assert go_messages == python_messages
    assert go_result.get("count") == len(python_messages)
