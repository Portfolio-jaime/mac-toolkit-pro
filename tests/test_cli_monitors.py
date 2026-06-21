from click.testing import CliRunner
from mac_toolkit_pro.cli import cli
from unittest.mock import patch, MagicMock


def test_battery_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["battery", "--help"])
    assert result.exit_code == 0
    assert "battery" in result.output.lower()


def test_system_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["system", "--help"])
    assert result.exit_code == 0
    assert "system" in result.output.lower()


def test_processes_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["processes", "--help"])
    assert result.exit_code == 0


def test_network_command_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["network", "--help"])
    assert result.exit_code == 0
