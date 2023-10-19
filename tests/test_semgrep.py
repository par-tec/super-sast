# -*- coding: utf-8 -*-

from pathlib import Path

import pytest

from entrypoint import TOOLS_MAP, run_sast

DATA_DIR = Path(__file__).parent / "data"
SEMGREP_DIR = DATA_DIR / "semgrep-01"


def test_semgrep_ignore(log_file, monkeypatch):
    expected_pylist = [SEMGREP_DIR / "init.py", SEMGREP_DIR / "simple.py"]

    monkeypatch.chdir(SEMGREP_DIR.as_posix())

    with log_file.open("a") as log_fh:
        # Run Semgrep tool
        run_sast(
            tool="semgrep",
            command=TOOLS_MAP["semgrep"],
            env={
                "HOME": "/tmp",
                "USER": "nobody",
                "RUN_ALL_TOOLS": "false",
                "RUN_SEMGREP": "true",
                "SEMGREP_ARGS": "--verbose",
                "PATH": (
                    "/usr/local/bin:/usr/local/sbin:" "/usr/sbin:/usr/bin:/sbin:/bin"
                ),
            },
            config_dir=Path("/code/config"),
            log_file=log_fh,
        )

    log_file_content = log_file.read_text()

    assert "Skipped by .semgrepignore:" in log_file_content
    for expected in expected_pylist:
        assert (
            f"Ignoring {expected.absolute().as_posix()} due to .semgrepignore"
            in log_file_content
        )


@pytest.fixture
def log_file():
    log_file = SEMGREP_DIR / "semgrep.log"
    if log_file.exists():
        log_file.unlink()
    yield log_file
    # We are not removing log_file because if the test fails
    # we want to check the content.
