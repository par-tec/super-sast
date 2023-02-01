from pathlib import Path

import pytest

from entrypoint import POM, TOOLS_MAP, run_sast

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


def test_pom_parse():
    pom_xml = DATA_DIR / "src-pom.xml"
    dst_xml = DATA_DIR / "dest-pom.xml"
    src_pom = POM(pom_xml)
    dst_pom = POM(dst_xml)
    assert src_pom.ns
    assert dst_pom.ns


def test_pom_get_plugins():
    testcases = [
        ("src-pom.xml", 3),
        ("dest-pom.xml", 4),
    ]
    for f, count in testcases:
        pom_xml = DATA_DIR / f
        pom = POM(pom_xml)
        plugins = pom.plugins()
        plugins_id = [
            (pom.find("artifactId", p).text + ":" + pom.find("groupId", p).text)
            for p in plugins
        ]
        assert len(plugins_id) == count


def test_pom_replace_ns():
    testcases = [("src-pom.xml", "dest-pom-1.xml"), ("src-pom.xml", "dest-pom-2.xml")]
    for f, dst in testcases:
        pom_xml = DATA_DIR / f
        pom = POM(pom_xml)
        dst_pom = POM(DATA_DIR / dst)
        pom.replace_ns(pom.root, dst_pom.ns)
        pom.ns = dst_pom.ns
        src_plugins = pom.plugins()
        assert len(src_plugins) == 3
        dst_plugins_tag = dst_pom.plugins_tag()
        for p in src_plugins:
            dst_plugins_tag.append(p)
        assert len(dst_pom.plugins()) == 7
        dst_pom.write("tests/deleteme-out.xml")


def test_pom_append_plugins():
    testcases = [("dest-pom.xml", 4), ("dest-pom-1.xml", 4), ("dest-pom-2.xml", 4)]

    pom_xml = DATA_DIR / "src-pom.xml"
    for f, count in testcases:
        dst_xml = DATA_DIR / f
        dst_pom = POM(dst_xml)
        dst_pom.add_plugins_from_pom(pom_xml.absolute().as_posix())

        # Total plugins count.
        dst_plugins = dst_pom.plugins()
        assert len(dst_plugins) == 3 + count

        # Use default namespace.
        dst_pom.write("tests/deleteme-out.xml")
        content = Path("tests/deleteme-out.xml").read_text()
        assert "ns0:" not in content
