"""
Run various SAST tools.
"""
import logging
import os
import shlex
import sys
from pathlib import Path
from subprocess import run

import pytest

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TOOLS_MAP = {
    "trivy_config": {
        "cmdline": "trivy --config {config_file} config .",
        "config_file": "trivy.yaml",
    },
    "trivy_filesystem": {
        "cmdline": "trivy --config {config_file} filesystem .",
        "config_file": "trivy.yaml",
    },
    "bandit": {
        "cmdline": "bandit --config {config_file} {args} -r .",
        "config_file": "bandit.yaml",
    },
    "safety": {
        "cmdline": "safety {args} check",
        "config_file": "safety.yaml",
    },
    "kubescape": {
        "cmdline": "kubescape {args} scan .",
        "args": "--cache-dir /tmp",
    },
    "checkov": {
        "cmdline": "checkov --config-file {config_file} {args} --directory .",
        "config_file": ".checkov.yaml",
    },
    "semgrep": {
        "cmdline": "semgrep --config {config_file} {args} .",
        "config_file": "string://auto",
    },
    "spotbugs": {
        "cmdline": "mvn com.github.spotbugs:spotbugs-maven-plugin:check",
    },
    "owasp_dependency_check": {
        "cmdline": "mvn org.owasp:dependency-check-maven:check",
    },
    "spotless_check": {
        "cmdline": "mvn com.diffplug.spotless:spotless-maven-plugin:check",
    },
    "spotless_apply": {
        "cmdline": "mvn com.diffplug.spotless:spotless-maven-plugin:apply",
    },
}


def run_sast(tool, command, env, config_dir):
    def _localize(path):
        if not path:
            return ""
        if path.startswith("string://"):
            return path[9:]
        return (config_dir / path).absolute().as_posix()

    log.info(f"Running {tool}")
    var_enabled = f"RUN_{tool.upper()}"
    var_args = f"{tool.upper()}_ARGS"
    var_config_file = f"{tool.upper()}_CONFIG_FILE"

    env_enabled = env.get(var_enabled, "true")
    env_args = env.get(var_args, "")
    env_config_file = env.get(var_config_file, "")
    log.info(
        f"""
    {var_enabled}={env_enabled}
    {var_args}={env_args}
    {var_config_file}={env_config_file}
    """
    )

    if env_enabled.lower() != "true":
        log.info(f"Skipping {tool}")
        return

    cmdline = command["cmdline"]
    config_file = env_config_file or _localize(command.get("config_file", ""))
    args = env_args or command.get("args", "")
    cmd = cmdline.format(
        args=args,
        config_file=config_file,
    )
    log.warning(f"Running {cmd}")
    run(
        shlex.split(cmd),
        shell=False,
        stdout=Path("stdout.log").open("a"),
        stderr=Path("stderr.log").open("a"),
        check=True,
        env=env,
    )


if __name__ == "__main__":
    # open environment variables
    try:
        config_dir = Path(sys.argv[1])
        if not config_dir.is_dir():
            raise OSError(f"Config directory {config_dir} does not exist")
    except IndexError:
        config_dir = Path("/app/config")

    for tool, command in TOOLS_MAP.items():
        run_sast(tool, command, os.environ, config_dir=config_dir)


# A parameterized test for each TOOLS_MAP entry
@pytest.mark.parametrize("tool,command", TOOLS_MAP.items())
def test_tools(tool, command):
    run_sast(
        tool=tool,
        command=command,
        env={
            "HOME": "/tmp",
            "USER": "nobody",
            "PATH": ("/usr/local/bin:/usr/local/sbin:" "/usr/sbin:/usr/bin:/sbin:/bin"),
        },
        config_dir=Path("/code/config"),
    )
