"""Tests for the Typer CLI application."""

from typer.testing import CliRunner
from smilesherlock.cli.main import app

runner = CliRunner()

def test_app_version():
    """Test the version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "SmileSherlock" in result.stdout
    assert "License: MIT" in result.stdout
    assert "Repository:" in result.stdout

def test_app_status():
    """Test the status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "SmileSherlock Status" in result.stdout
    assert "Configuration" in result.stdout
    assert "Cache Dir" in result.stdout

def test_app_lookup_missing_argument():
    """Test lookup command fails gracefully when missing query."""
    result = runner.invoke(app, ["lookup"])
    assert result.exit_code != 0
    assert "Missing argument" in result.stdout