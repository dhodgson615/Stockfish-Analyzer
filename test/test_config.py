"""Tests for the configuration module."""

import json
import os
import tempfile

import pytest

import src.config as config


def test_engine_config_defaults():
    """Test that EngineConfig has correct default values."""
    cfg = config.EngineConfig()

    assert cfg.engine_path == "/usr/games/stockfish"
    assert cfg.threads == 4
    assert cfg.hash_size == 16384
    assert cfg.skill_level == 20
    assert cfg.eval_depth == 18
    assert cfg.syzygy_path.endswith("chess/syzygy")  # Expanded path


def test_engine_config_post_init():
    """Test that __post_init__ expands user paths."""
    cfg = config.EngineConfig(syzygy_path="~/test/path")

    assert cfg.syzygy_path == os.path.expanduser("~/test/path")


def test_create_argument_parser():
    """Test that argument parser is created correctly."""
    parser = config.create_argument_parser()

    # Test help doesn't crash
    with pytest.raises(SystemExit):  # argparse calls sys.exit for help
        parser.parse_args(['--help'])


def test_parse_config_defaults():
    """Test parsing with no arguments uses defaults."""
    cfg = config.parse_config([])

    assert cfg.engine_path == "/usr/games/stockfish"
    assert cfg.threads == 4
    assert cfg.hash_size == 16384
    assert cfg.skill_level == 20
    assert cfg.eval_depth == 18


def test_parse_config_cli_args():
    """Test parsing with CLI arguments."""
    args = [
        "--engine-path",
        "/custom/engine",
        "--threads",
        "8",
        "--hash-size",
        "8192",
        "--skill-level",
        "15",
        "--depth",
        "12",
        "--syzygy-path",
        "/custom/syzygy",
    ]
    
    cfg = config.parse_config(args)
    
    assert cfg.engine_path == "/custom/engine"
    assert cfg.threads == 8
    assert cfg.hash_size == 8192
    assert cfg.skill_level == 15
    assert cfg.eval_depth == 12
    assert cfg.syzygy_path == "/custom/syzygy"


def test_parse_config_skill_level_validation():
    """Test that skill level is validated correctly."""
    # Valid skill level
    cfg = config.parse_config(['--skill-level', '10'])
    assert cfg.skill_level == 10
    
    # Invalid skill level should raise SystemExit (argparse error)
    with pytest.raises(SystemExit):
        config.parse_config(['--skill-level', '21'])
    
    with pytest.raises(SystemExit):
        config.parse_config(['--skill-level', '-1'])


def test_save_and_load_config_file():
    """Test saving and loading configuration files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.json")
        
        # Create a custom config
        original_cfg = config.EngineConfig(
            engine_path="/test/engine",
            threads=6,
            hash_size=4096,
            skill_level=18,
            eval_depth=15,
            syzygy_path="/test/syzygy"
        )
        
        # Save config
        config.save_config_file(original_cfg, config_path)
        
        # Verify file exists and has correct content
        assert os.path.exists(config_path)
        
        with open(config_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['engine_path'] == "/test/engine"
        assert saved_data['threads'] == 6
        assert saved_data['hash_size'] == 4096
        assert saved_data['skill_level'] == 18
        assert saved_data['eval_depth'] == 15
        assert saved_data['syzygy_path'] == "/test/syzygy"
        
        # Load config from file
        loaded_data = config.load_config_file(config_path)
        
        assert loaded_data == saved_data


def test_parse_config_with_config_file():
    """Test parsing with config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test.json")
        
        # Create config file
        config_data = {
            "engine_path": "/file/engine",
            "threads": 12,
            "hash_size": 2048,
            "skill_level": 16,
            "eval_depth": 22
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Parse config from file
        cfg = config.parse_config(['--config', config_path])
        
        assert cfg.engine_path == "/file/engine"
        assert cfg.threads == 12
        assert cfg.hash_size == 2048
        assert cfg.skill_level == 16
        assert cfg.eval_depth == 22


def test_parse_config_cli_overrides_file():
    """Test that CLI arguments override config file settings."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test.json")
        
        # Create config file
        config_data = {
            "threads": 4,
            "eval_depth": 15
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Parse with CLI override
        cfg = config.parse_config([
            '--config', config_path,
            '--threads', '8'  # Override threads, keep eval_depth from file
        ])
        
        assert cfg.threads == 8  # From CLI
        assert cfg.eval_depth == 15  # From file


def test_load_config_file_not_found():
    """Test loading non-existent config file raises error."""
    with pytest.raises(FileNotFoundError):
        config.load_config_file("/nonexistent/config.json")


def test_load_config_file_invalid_json():
    """Test loading invalid JSON raises error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "invalid.json")
        
        with open(config_path, 'w') as f:
            f.write("{ invalid json content")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            config.load_config_file(config_path)


def test_load_config_file_invalid_fields():
    """Test loading config with invalid fields shows warning and filters them."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "invalid_fields.json")
        
        config_data = {
            "threads": 8,
            "invalid_field": "should_be_ignored",
            "another_invalid": 123
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Should not raise error, but filter invalid fields
        loaded_data = config.load_config_file(config_path)
        
        assert "threads" in loaded_data
        assert "invalid_field" not in loaded_data
        assert "another_invalid" not in loaded_data


def test_save_config_creates_directory():
    """Test that save_config_file creates parent directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        nested_path = os.path.join(temp_dir, "nested", "dir", "config.json")
        
        cfg = config.EngineConfig()
        config.save_config_file(cfg, nested_path)
        
        assert os.path.exists(nested_path)


def test_parse_config_save_config_exits():
    """Test that --save-config option saves and exits."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "save_test.json")
        
        # Should exit after saving
        with pytest.raises(SystemExit):
            config.parse_config(['--save-config', config_path])
        
        # Verify file was created
        assert os.path.exists(config_path)


def test_get_default_config():
    """Test get_default_config function."""
    cfg = config.get_default_config()
    
    assert isinstance(cfg, config.EngineConfig)
    assert cfg.engine_path == "/usr/games/stockfish"
    assert cfg.threads == 4