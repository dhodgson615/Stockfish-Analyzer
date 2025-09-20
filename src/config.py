"""Configuration management for Stockfish-Analyzer.

This module handles CLI arguments, config files, and provides a centralized
configuration system for all engine and application settings.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, cast


@dataclass
class EngineConfig:
    """Configuration settings for the Stockfish engine and
    application.
    """

    # Engine binary settings
    engine_path: str = "/usr/games/stockfish"

    # Engine performance settings
    threads: int = 4
    hash_size: int = 16384  # MB
    skill_level: int = 20
    eval_depth: int = 18

    # Tablebase settings
    syzygy_path: str = "~/chess/syzygy"

    def __post_init__(self) -> None:
        """Expand user paths after initialization."""
        self.syzygy_path = os.path.expanduser(self.syzygy_path)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Interactive chess analysis with Stockfish engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 src/main.py
  python3 src/main.py --engine-path /usr/local/bin/stockfish
  python3 src/main.py --threads 8 --hash-size 8192 --depth 20
  python3 src/main.py --config my_config.json
  python3 src/main.py --skill-level 15 --syzygy-path ~/tablebase/syzygy

Config file format (JSON):
{
    "engine_path": "/usr/local/bin/stockfish",
    "threads": 8,
    "hash_size": 8192,
    "skill_level": 20,
    "eval_depth": 20,
    "syzygy_path": "~/chess/syzygy"
}
        """,
    )

    # Engine binary settings
    parser.add_argument(
        "--engine-path",
        type=str,
        help="Path to Stockfish engine binary (default: /usr/games/stockfish)",
    )

    # Engine performance settings
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of threads for engine to use (default: 4)",
    )

    parser.add_argument(
        "--hash-size", type=int, help="Hash table size in MB (default: 16384)"
    )

    parser.add_argument(
        "--skill-level",
        type=int,
        choices=range(0, 21),
        help="Engine skill level 0-20, where 20 is strongest (default: 20)",
    )

    parser.add_argument(
        "--depth",
        "--eval-depth",
        type=int,
        dest="eval_depth",
        help="Evaluation depth in plies (default: 18)",
    )

    # Tablebase settings
    parser.add_argument(
        "--syzygy-path",
        type=str,
        help="Path to Syzygy tablebase files (default: ~/chess/syzygy)",
    )

    # Config file support
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file with engine settings",
    )

    # Output config
    parser.add_argument(
        "--save-config",
        type=str,
        help="Save current settings to JSON config file and exit",
    )

    return parser


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            config_data = cast(Dict[str, Any], json.load(f))

        # Validate that all keys are valid EngineConfig fields
        valid_fields = set(
            EngineConfig.__dataclass_fields__.keys()
        )  # TODO: fix whatever nresolved attribute reference '__dataclass_fields__' for class 'EngineConfig' is
        invalid_fields = set(config_data.keys()) - valid_fields

        if invalid_fields:
            print(
                f"Warning: Unknown config fields will be ignored: "
                f"{invalid_fields}"
            )
            # Remove invalid fields
            config_data = {
                k: v for k, v in config_data.items() if k in valid_fields
            }

        return config_data

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")

    except Exception as e:
        raise ValueError(f"Error reading config file {config_path}: {e}")


def save_config_file(config: EngineConfig, config_path: str) -> None:
    """Save configuration to a JSON file."""
    try:
        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(asdict(config), f, indent=2)

        print(f"Configuration saved to: {config_path}")

    except Exception as e:
        raise ValueError(f"Error saving config file {config_path}: {e}")


def parse_config(args: Optional[list[str]] = None) -> EngineConfig:
    """Parse command-line arguments and config files to create final
    configuration.

    Args:
        args: Optional list of command-line arguments. If None, uses
            sys.argv.

    Returns:
        EngineConfig object with all settings resolved.

    Precedence order (highest to lowest):
    1. Command-line arguments
    2. Config file settings (if --config specified)
    3. Default values
    """
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)

    # Start with default configuration
    config = EngineConfig()

    # Load config file if specified
    if parsed_args.config:
        try:
            file_config = load_config_file(parsed_args.config)

            # Update config with file values
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration...")

    # Override with command-line arguments (highest precedence)
    for key, value in vars(parsed_args).items():
        if value is not None and key not in ["config", "save_config"]:
            if hasattr(config, key):
                setattr(config, key, value)

    # Handle save-config option
    if parsed_args.save_config:
        save_config_file(config, parsed_args.save_config)
        exit(0)

    # Expand paths after all settings are resolved
    config.__post_init__()
    
    return config


def get_default_config() -> EngineConfig:
    """Get default configuration without parsing any arguments."""
    return EngineConfig()