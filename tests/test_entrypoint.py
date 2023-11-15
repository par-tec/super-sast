from pathlib import Path

import pytest

from entrypoint import TOOLS_MAP, run_sast

DATA_DIR = Path(__file__).parent / "data"


# A parameterized test for each TOOLS_MAP entry
@pytest.mark.parametrize("tool,command", TOOLS_MAP.items())
def test_tools(tool, command):
    run_sast(
        tool=tool,
        command=command,
        env={
            "HOME": "/tmp",
            "USER": "nobody",
            "BANDIT_CONFIG_FILE": "/code/config/bandit.yaml",
            "PATH": ("/usr/local/bin:/usr/local/sbin:" "/usr/sbin:/usr/bin:/sbin:/bin"),
        },
        config_dir=Path("/code/config"),
    )


def test_mvn_fail():
    tool = "spotless_check"
    command = TOOLS_MAP[tool]
    status = run_sast(
        tool=tool,
        command=command,
        env={
            "HOME": "/tmp",
            "USER": "nobody",
            "MAVEN_ARGS": "-f /foo.xml",
            "BANDIT_CONFIG_FILE": "/code/config/bandit.yaml",
            "PATH": ("/usr/local/bin:/usr/local/sbin:" "/usr/sbin:/usr/bin:/sbin:/bin"),
        },
        config_dir=Path("/code/config"),
    )
    assert status == 2


def test_mvn_skip():
    tool = "spotless_check"
    command = TOOLS_MAP[tool]
    status = run_sast(
        tool=tool,
        command=command,
        env={
            "HOME": "/tmp",
            "USER": "nobody",
            "BANDIT_CONFIG_FILE": "/code/config/bandit.yaml",
            "PATH": ("/usr/local/bin:/usr/local/sbin:" "/usr/sbin:/usr/bin:/sbin:/bin"),
        },
        config_dir=Path("/code/config"),
    )
    assert status == 0
