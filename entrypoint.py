"""
Run various SAST tools.
"""
import logging
import os
import shlex
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from sys import stderr, stdout

# Log to stdout
# for both stdout and stderr.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

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
    #  TODO: conftest
    #  TODO: talisman
}


def _localize(path, config_dir):
    if not path:
        return ""
    if path.startswith("string://"):
        return path[9:]
    return (config_dir / path).absolute().as_posix()


def run_sast(tool, command, env, config_dir, log_file=stdout):
    log.info(f"Preparing {tool}")

    var_enabled = f"RUN_{tool.upper()}"
    var_args = f"{tool.upper()}_ARGS"
    var_config_file = f"{tool.upper()}_CONFIG_FILE"

    env_enabled = env.get(var_enabled, "true")
    env_args = env.get(var_args, "")
    env_config_file = env.get(var_config_file, "")

    default_args = command.get("args", "")
    default_config_file = _localize(command.get("config_file", ""), config_dir)

    if env_enabled.lower() != "true":
        log.info(f"Skipping {tool}")
        return

    cmdline = command["cmdline"]
    config_file = env_config_file or default_config_file
    cmd_args = env_args or default_args
    cmd = cmdline.format(
        args=cmd_args,
        config_file=config_file,
    )
    log.info(f"Running {cmd}")

    status = subprocess.run(
        shlex.split(cmd),
        shell=False,
        stdout=log_file,
        stderr=log_file,
        check=False,  # Don't raise exception on non-zero exit code.
        timeout=600,
        env=env,
    )
    if status.returncode != 0:
        log.error(f"{tool} failed with status {status.returncode}")
    return status.returncode


def _show_environ(config_dir, dump_config=False):
    env = os.environ
    print("Environment variables:")
    print("""|Variable|Default|Tool|""")
    print("""|--------|-------|----|""")
    for tool, command in TOOLS_MAP.items():
        var_enabled = f"RUN_{tool.upper()}"
        var_args = f"{tool.upper()}_ARGS"
        var_config_file = f"{tool.upper()}_CONFIG_FILE"

        env_enabled = env.get(var_enabled, "true")
        env_args = env.get(var_args, "")
        env_config_file = env.get(var_config_file, "")

        default_args = command.get("args", "")
        default_config_file = _localize(
            command.get("config_file", ""), config_dir=config_dir
        )
        if dump_config:
            print(
                f"""
            # {tool}
            {var_enabled}={env_enabled}
            {var_args}={env_args or default_args}  # {default_args}
            {var_config_file}="{env_config_file or default_config_file}"  # {default_config_file}
            """
            )
            continue
        print(f"""|{var_enabled}|{env_enabled}|{tool}|""")
        if default_args:
            print(f"""|{var_args}|{default_args}|{tool}|""")
        if default_config_file:
            print(f"""|{var_config_file}|{default_config_file}|{tool}|""")
    exit(2)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--config-dir",
        help="Directory containing config files",
        default="/app/config",
    )
    parser.add_argument(
        "--environs",
        help="Environment variables to pass to the tools",
        default="",
        action="store_true",
    )
    parser.add_argument(
        "--dump-config",
        help="Environment variables to pass to the tools",
        default="",
        action="store_true",
    )
    args = parser.parse_args()

    if args.environs or args.dump_config:
        _show_environ(Path(args.config_dir), dump_config=args.dump_config)
    tee = subprocess.Popen(
        ["/usr/bin/tee", "super-sast.log"], shell=False, stdin=subprocess.PIPE
    )
    # Cause tee's stdin to get a copy of our stdin/stdout (as well as that
    # of any child processes we spawn)
    os.dup2(tee.stdin.fileno(), stdout.fileno())
    os.dup2(tee.stdin.fileno(), stderr.fileno())
    sast_status = {}
    for tool, command in TOOLS_MAP.items():
        status = run_sast(
            tool,
            command,
            os.environ.copy(),
            config_dir=Path(args.config_dir),
            log_file=stdout,
        )
        sast_status[tool] = status
    log.info("All tools finished")
    log.info(sast_status)
