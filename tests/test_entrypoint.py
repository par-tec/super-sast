from pathlib import Path

import pytest

from entrypoint import TOOLS_MAP, get_pom_build_plugins, run_sast


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


def test_parse_pom():
    pom_xml = Path(__file__).parent / "src-pom.xml"
    dest_xml = Path(__file__).parent / "dest-pom.xml"
    src_plugins = get_pom_build_plugins(pom_xml)
    assert src_plugins is not None
    dest_plugins = get_pom_build_plugins(dest_xml)
    assert dest_plugins is not None
    raise NotImplementedError
