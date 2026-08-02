"""Tests for the Typer CLI application."""

from typer.testing import CliRunner
from smilesherlock.cli.main import app

# mix_stderr=True ensures error messages are captured in result.output
runner = CliRunner(mix_stderr=True) 

def test_app_version():
    """Test the version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "SmileSherlock" in result.output
    assert "License: MIT" in result.output
    assert "Repository:" in result.output

def test_app_status():
    """Test the status command."""
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "SmileSherlock Status" in result.output
    assert "Configuration" in result.output
    assert "Cache Dir" in result.output

def test_app_lookup_missing_argument():
    """Test lookup command fails gracefully when missing query."""
    result = runner.invoke(app, ["lookup"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output