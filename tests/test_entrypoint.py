from pathlib import Path

import pytest

from entrypoint import POM, TOOLS_MAP, run_sast


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


def test_pom_parse():
    pom_xml = Path(__file__).parent / "src-pom.xml"
    dst_xml = Path(__file__).parent / "dest-pom.xml"
    src_pom = POM(pom_xml)
    dst_pom = POM(dst_xml)
    assert src_pom.ns
    assert dst_pom.ns


def test_pom_get_plugins():
    pom_xml = Path(__file__).parent / "src-pom.xml"
    pom = POM(pom_xml)
    plugins = pom.findall(".//build/plugins/plugin")
    assert len(plugins) == 3


def test_pom_append_plugins():
    pom_xml = Path(__file__).parent / "src-pom.xml"
    dst_xml = Path(__file__).parent / "dest-pom.xml"
    dst_pom = POM(dst_xml)
    dst_pom.add_plugins_from_pom(pom_xml.absolute().as_posix())
    dst_plugins = dst_pom.plugins()
    assert len(dst_plugins) == 6
    dst_pom.write("tests/deleteme-out.xml")
