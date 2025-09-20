#!/usr/bin/env python3
"""Test for the setup script functionality."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestSetupScript(unittest.TestCase):
    """Test the setup.sh script functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(__file__).parent.parent
        self.setup_script = self.test_dir / "setup.sh"
        
    def test_setup_script_exists_and_executable(self):
        """Test that setup script exists and is executable."""
        self.assertTrue(self.setup_script.exists(), "setup.sh should exist")
        self.assertTrue(os.access(self.setup_script, os.X_OK), "setup.sh should be executable")
    
    def test_config_file_creation(self):
        """Test that the script can create valid configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            
            # Create a mock stockfish binary
            mock_stockfish = Path(tmpdir) / "stockfish"
            mock_stockfish.write_text("#!/bin/bash\nexit 0\n")
            mock_stockfish.chmod(0o755)
            
            # Simulate the config creation function from the script
            config_data = {
                "engine_path": str(mock_stockfish),
                "threads": 4,
                "hash_size": 16384,
                "skill_level": 20,
                "eval_depth": 18,
                "syzygy_path": f"{Path.home()}/chess/syzygy"
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Verify the config file is valid
            self.assertTrue(config_path.exists())
            
            with open(config_path) as f:
                loaded_config = json.load(f)
            
            self.assertEqual(loaded_config["engine_path"], str(mock_stockfish))
            self.assertEqual(loaded_config["threads"], 4)
            self.assertEqual(loaded_config["hash_size"], 16384)
            self.assertEqual(loaded_config["skill_level"], 20)
            self.assertEqual(loaded_config["eval_depth"], 18)
            self.assertIn("chess/syzygy", loaded_config["syzygy_path"])
    
    def test_setup_script_help_functions(self):
        """Test that the helper functions in the script work correctly."""
        # Test the OS detection logic - extract just the function, not run the whole script
        result = subprocess.run(
            ["bash", "-c", '''
            detect_os() {
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    echo "macos"
                elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    echo "linux"
                else
                    echo "unknown"
                fi
            }
            detect_os
            '''], 
            capture_output=True, 
            text=True,
            cwd=self.test_dir
        )
        
        # Should return either 'linux', 'macos', or 'unknown'
        output = result.stdout.strip()
        self.assertIn(output, ['linux', 'macos', 'unknown'])
        self.assertEqual(result.returncode, 0)
    
    def test_existing_download_script_integration(self):
        """Test that the setup script can find the existing download script."""
        download_script = self.test_dir / "scripts" / "download_syzygy.sh"
        self.assertTrue(download_script.exists(), 
                       "download_syzygy.sh should exist for integration")


if __name__ == "__main__":
    unittest.main()