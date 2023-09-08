"""
Run various SAST tools.

This script is intended to be run as a Docker entrypoint
and can be tested with the following command:

        pytest -v

It only uses the standard library and has no dependencies.
"""
import logging
import os
import re
import shlex
import subprocess
import sys
import uuid
from argparse import ArgumentParser
from pathlib import Path
from shutil import copytree
from sys import stderr, stdout
from xml.etree import ElementTree

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
        "cmdline": "safety check {args}",
        "args": "-r requirements.txt",
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
        "cmdline": "mvn {maven_args} com.github.spotbugs:spotbugs-maven-plugin:check",
    },
    "owasp_dependency_check": {
        "cmdline": "mvn {maven_args} org.owasp:dependency-check-maven:check",
    },
    "spotless_check": {
        "cmdline": "mvn {maven_args} com.diffplug.spotless:spotless-maven-plugin:check",
    },
    "spotless_apply": {
        "cmdline": "mvn {maven_args} com.diffplug.spotless:spotless-maven-plugin:apply",
    },
    #  TODO: conftest
    #  TODO: talisman
}


class POM:
    def __init__(self, pom_xml):
        self.pom_xml = pom_xml
        self.pom_tree = ElementTree.parse(pom_xml)
        self.root = self.pom_tree.getroot()
        self.ns = (
            self.root.tag.split("}")[0][1:]
            if self.root.tag and self.root.tag.startswith("{")
            else ""
        )

        self.TAG_BUILD = self.to_ns("build")
        self.TAG_PLUGINS = self.to_ns("plugins")

    @staticmethod
    def plugin_id(plugin):
        ns = plugin.tag.split("}")[0][1:] if plugin.tag.startswith("{") else ""

        def _find_or_none(field, ns):
            tag = plugin.find(POM._to_ns(field, ns))
            if tag is not None and tag.text:
                return tag.text
            return None

        return tuple(
            _find_or_none(field, ns)
            for field in (
                "groupId",
                "artifactId",
                "version",
            )
        )

    @staticmethod
    def _to_ns(tag, ns):
        return f"{{{ns}}}{tag}" if ns else tag

    def to_ns(self, tag):
        return POM._to_ns(tag, self.ns)

    def find(self, tag, parent=None):
        parent = parent or self.root
        return parent.find(self.to_ns(tag))

    def findall(self, xpath, parent=None):
        parent = parent or self.root
        xpath = re.sub(r"(\w+)", rf"{{{self.ns}}}\1", xpath) if self.ns else xpath
        return parent.findall(xpath)

    def plugins(self):
        return self.findall(".//build/plugins/plugin")

    def plugins_tag(self):
        return self.findall(".//build/plugins")[0]

    def add_plugins(self, plugins):
        if not plugins:
            return
        build = self.find("build")
        # Add build tag if it doesn't exist.
        if not build:
            build = ElementTree.SubElement(self.root, self.TAG_BUILD)
        plugins_tag = self.find("plugins", build)
        # Add plugins tag if it doesn't exist.
        if not plugins_tag:
            plugins_tag = ElementTree.SubElement(build, self.TAG_PLUGINS)

        dst_plugins = {(g, a): v for g, a, v in map(POM.plugin_id, self.plugins())}
        for plugin in plugins:
            # Apply the destination pom namespace to the plugin.
            *target_plugin, target_version = POM.plugin_id(plugin)
            POM.replace_ns(plugin, self.ns)
            # Ensure that the plugin doesn't already exist.
            existing_version = dst_plugins.get(tuple(target_plugin))
            if not existing_version:
                log.info(f"Adding plugin {POM.plugin_id(plugin)}")
                plugins_tag.append(plugin)
                continue
            if existing_version == target_version:
                log.info(f"Plugin {POM.plugin_id(plugin)} already exists. Skipping.")
                continue
            if existing_version != target_version:
                raise ValueError(
                    f"Plugin {target_plugin} already exists with version {existing_version}"
                )

    def validate_plugins(self, plugins):
        dst_plugins = {(g, a): v for g, a, v in map(POM.plugin_id, self.plugins())}
        src_plugins = {(g, a): v for g, a, v in map(POM.plugin_id, plugins)}
        for plugin_id, version in src_plugins.items():
            if plugin_id in dst_plugins and dst_plugins[plugin_id] != version:
                raise ValueError(
                    f"Plugin {plugin_id} already exists with version {dst_plugins[plugin_id]}"
                )

    @staticmethod
    def replace_ns(element, new_ns):
        if element.tag.startswith("{"):
            if new_ns:
                element.tag = f"{{{new_ns}}}{element.tag.split('}')[1]}"
            else:
                element.tag = element.tag.split("}")[1]
        elif new_ns:
            element.tag = f"{{{new_ns}}}{element.tag}"

        for child in element:
            POM.replace_ns(child, new_ns)

    def add_plugins_from_pom(self, src_pom_xml: str):
        src_pom = POM(src_pom_xml)
        src_plugins = src_pom.plugins()
        self.add_plugins(src_plugins)

    def write(self, fpath: str):
        ElementTree.register_namespace("", self.ns)
        self.pom_tree.write(fpath, encoding="utf-8", xml_declaration=True)


def _localize(path, config_dir):
    if not path:
        return ""
    if path.startswith("string://"):
        return path[9:]
    return (config_dir / path).absolute().as_posix()


def exists_python_code(dir):
    py_files = [
        "setup.py",
        "tox.ini",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    ]

    for py_file in py_files:
        py_path = Path(dir).joinpath(py_file)
        if py_path.exists():
            return True

    return False


def run_sast(tool, command, env, config_dir, log_file=stdout, run_all=True):
    log.info(f"Preparing {tool}")

    var_enabled = f"RUN_{tool.upper()}"
    var_args = f"{tool.upper()}_ARGS"
    var_config_file = f"{tool.upper()}_CONFIG_FILE"

    env_enabled = env.get(var_enabled, "true" if run_all else "false")
    env_args = env.get(var_args, "")
    env_config_file = env.get(var_config_file, "")

    default_args = command.get("args", "")
    default_config_file = _localize(command.get("config_file", ""), config_dir)
    if env_enabled.lower() != "true":
        log.info(f"Skipping {tool}")
        return

    if tool.lower() == "safety":
        if not exists_python_code(os.getcwd()):
            log.info("Skipping safety because there are no python project descriptors")
            return

    cmdline = command["cmdline"]
    config_file = env_config_file or default_config_file
    cmd_args = env_args or default_args
    maven_args = env.get("MAVEN_ARGS", "")
    if (
        env.get("LOG_MAVEN_PROGRESS", "false") == "false"
        and "--no-transfer-progress" not in maven_args
    ):
        maven_args += " --no-transfer-progress "
    cmd = cmdline.format(
        args=cmd_args,
        config_file=config_file,
        maven_args=maven_args,
    )

    if cmd.startswith("mvn "):
        if " -f " in cmd:
            log.error(f"Skipping {tool} because it uses a custom pom.xml: {cmd}")
            return 2
        if not Path("pom.xml").is_file():
            log.info("Skipping maven command because pom.xml is missing")
            return 0
        dst_pom = POM("pom.xml")
        tmpfile = f".pom.xml.{uuid.uuid4()}"
        log.info("Creating runtime pom.xml in %r", (tmpfile,))
        dst_pom.add_plugins_from_pom("/app/java-validators/pom.xml")
        dst_pom.write(tmpfile)
        cmd = f"mvn -f {tmpfile} {cmd[3:]}"

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
    print("""|RUN_ALL_TOOLS|true|Run all tools|""")
    print("""|LOG_MAVEN_PROGRESS|false|Log maven progress|""")
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
    sys.exit(2)


def _copy_java_validators():
    m2_home = Path(os.environ.get("M2_HOME", "/tmp")) / ".m2"
    if m2_home.exists():
        log.warning(f"Directory {m2_home} already exists. Skipping copy.")
        return
    log.info(f"Copying java validators to {m2_home.absolute().as_posix()}")
    try:
        copytree("/app/java-validators/.m2", m2_home)
    except Exception as e:
        stat = os.stat(m2_home)
        log.error(
            "An exception occurred while copying java validators, context information below\n"
            f" - UID: {os.getuid()}\n - GID: {os.getgid()}\n"
            f" - Extra info about the error:\n  - Path: {m2_home.absolute().as_posix()}\n  - Permissions: {oct(stat.st_mode)[2:]}\n"
            f"  - Owner (user): {stat.st_uid} {f'({usr})' if (usr := os.getenv('USER')) else ''}\n  - Owner (group): {stat.st_gid}\n"
            f"  - CWD: {os.getenv('PWD', '')}\n"
            f" - Error -> {type(e).__name__}: {e}"
        )


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
    try:
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

        _copy_java_validators()
        run_all = os.environ.get("RUN_ALL_TOOLS", "true").lower() == "true"
        for tool, command in TOOLS_MAP.items():
            status = run_sast(
                tool,
                command,
                os.environ.copy(),
                config_dir=Path(args.config_dir),
                log_file=stdout,
                run_all=run_all,
            )
            sast_status[tool] = status
        log.info("All tools finished")
        log.info(sast_status)
    except Exception as e:
        log.error(
            "An exception occurred while running SAST, context information below\n"
            f" - UID: {os.getuid()}\n - GID: {os.getgid()}\n"
            f" - Error: {type(e).__name__} -> {e}"
        )
        raise e
