from click.testing import CliRunner
from mac_toolkit_pro.cli import cli


def test_status_command_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "domain" in result.output.lower() or "status" in result.output.lower()


def test_status_lists_all_domains():
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    for domain in ("ollama", "docker", "dev_caches", "xcode", "trash"):
        assert domain in result.output
