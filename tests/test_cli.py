"""Tests for the Typer CLI application."""

from pathlib import Path
from typer.testing import CliRunner
from smilesherlock.cli.main import app

# Initialize without the invalid mix_stderr argument
runner = CliRunner() 

def test_app_version():
    """Test the version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "SmileSherlock" in result.output
    assert "License:" in result.output
    assert "MIT" in result.output
    assert "Repository:" in result.output
    assert "AtharvaTilewale/SmileSherlock" in result.output

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

def test_app_lookup_compound_name():
    """Test lookup command for compound name returns SMILES."""
    result = runner.invoke(app, ["lookup", "aspirin"])
    assert result.exit_code == 0
    assert "CC(=O)OC1=CC=CC=C1C(=O)O" in result.output
    assert "2244" in result.output


def test_download_help_includes_gen():
    """Test that download --help exposes the --gen option."""
    result = runner.invoke(app, ["download", "--help"])
    assert result.exit_code == 0
    assert "--gen" in result.output or "-g" in result.output


def test_download_gen_all_single_smiles(tmp_path: Path):
    """Test download with --gen all for a single SMILES in 2D and 3D."""
    out_dir = tmp_path / "structs"
    
    # 3D SDF
    result = runner.invoke(app, ["download", "CCO", "--gen", "all", "--3d", "--format", "sdf", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert "Successfully generated" in result.output

    # 2D MOL
    result = runner.invoke(app, ["download", "c1ccccc1", "--gen", "all", "--2d", "--format", "mol", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert "Successfully generated" in result.output

    # 3D PDB
    result = runner.invoke(app, ["download", "CC(=O)O", "--gen", "all", "--3d", "--format", "pdb", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert "Successfully generated" in result.output


def test_download_gen_all_batch_file(tmp_path: Path):
    """Test download with --gen all on a batch file of SMILES."""
    smi_file = tmp_path / "compounds.smi"
    smi_file.write_text("c1ccccc1\nCCO\nCC(=O)O\n", encoding="utf-8")
    out_dir = tmp_path / "batch_out"

    result = runner.invoke(app, ["download", "--file", str(smi_file), "--gen", "all", "--3d", "--format", "sdf", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert "Batch processing complete" in result.output
    assert "Generated:" in result.output


def test_download_gen_missing_batch_file(tmp_path: Path):
    """Test download with --gen missing generates structures not found in PubChem."""
    smi_file = tmp_path / "compounds_missing.smi"
    # c1ccccc1 is in PubChem, a custom hypothetical SMILES might not have 3D or CID
    smi_file.write_text("c1ccccc1\nCC(C)(C)CC(=O)N1CCCCC1C(=O)O\n", encoding="utf-8")
    out_dir = tmp_path / "batch_missing_out"

    result = runner.invoke(app, ["download", "--file", str(smi_file), "--gen", "missing", "--3d", "--format", "sdf", "-o", str(out_dir)])
    assert result.exit_code == 0
    assert "Batch processing complete" in result.output


def test_download_gen_invalid_mode():
    """Test invalid --gen argument."""
    result = runner.invoke(app, ["download", "CCO", "--gen", "invalid_mode"])
    assert result.exit_code != 0
    assert "Invalid value for --gen" in result.output

def test_app_update_help():
    """Test update --help."""
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "Check for a newer version" in result.output
    assert "--check" in result.output
    assert "--yes" in result.output


def test_detect_install_source():
    """Test install source detector helper."""
    from smilesherlock.cli.main import _detect_install_source
    source_type, detail = _detect_install_source()
    assert source_type in ["git_repo", "git_pip", "pip"]
    assert detail is not None
