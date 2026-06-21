from unittest.mock import patch
from mac_toolkit_pro.menu import MENU_CHOICES, show_menu


def test_menu_choices_not_empty():
    assert len(MENU_CHOICES) > 0


def test_menu_choices_have_required_keys():
    for choice in MENU_CHOICES:
        assert "name" in choice
        assert "value" in choice


def test_menu_includes_monitors():
    values = [c["value"] for c in MENU_CHOICES]
    assert "battery" in values
    assert "system" in values
    assert "processes" in values
    assert "network" in values


def test_menu_includes_toolkit_actions():
    values = [c["value"] for c in MENU_CHOICES]
    assert "analyze" in values
    assert "clean" in values


def test_show_menu_exits_on_quit():
    with patch("questionary.select") as mock_select:
        mock_select.return_value.ask.return_value = "❌ Quit"
        show_menu()


def test_toolkit_no_args_calls_show_menu():
    from click.testing import CliRunner
    from mac_toolkit_pro.cli import cli
    runner = CliRunner()
    with patch("mac_toolkit_pro.menu.show_menu") as mock_menu:
        mock_menu.return_value = None
        result = runner.invoke(cli, [])
    mock_menu.assert_called_once()
