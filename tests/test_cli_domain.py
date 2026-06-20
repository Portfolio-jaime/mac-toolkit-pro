import click
import pytest
from click.testing import CliRunner
from mac_toolkit_pro.cli import cli, ALL_ANALYZERS, _filter_analyzers


def test_filter_analyzers_none_returns_all():
    assert _filter_analyzers(None) == ALL_ANALYZERS


def test_filter_analyzers_valid_domain():
    result = _filter_analyzers("disk")
    assert len(result) == 1
    assert result[0].__self__.domain == "disk"


def test_filter_analyzers_invalid_domain_raises():
    with pytest.raises(click.BadParameter):
        _filter_analyzers("nonexistent_domain")


def test_analyze_domain_flag_runs():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--domain", "disk"])
    assert result.exit_code == 0


def test_analyze_invalid_domain_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--domain", "fakefakefake"])
    assert result.exit_code != 0
