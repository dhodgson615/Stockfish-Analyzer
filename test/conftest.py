import os
import subprocess

import chess
import pytest


@pytest.fixture
def new_board() -> chess.Board:
    """Returns a fresh chess board in the starting position."""
    return chess.Board()


@pytest.fixture
def checkmate_board() -> chess.Board:
    """Returns a board with a checkmate position (fool's mate)."""
    board = chess.Board()

    for move in ["f2f3", "e7e5", "g2g4", "d8h4"]:
        board.push(chess.Move.from_uci(move))

    return board


@pytest.fixture
def stalemate_board() -> chess.Board:
    """Returns a board with a stalemate position."""
    return chess.Board("8/8/8/8/8/5k2/7p/7K w - - 0 1")


@pytest.fixture
def sample_moves() -> list[chess.Move]:
    """Returns a list of sample chess moves."""
    return [chess.Move.from_uci(m) for m in ["e2e4", "d2d4", "g1f3"]]


@pytest.fixture
def engine_path() -> str:
    """Returns path to Stockfish engine, checking multiple common locations."""
    # Check multiple possible locations for Stockfish on macOS
    macos_paths = [
        "/opt/homebrew/bin/stockfish",  # Apple Silicon Mac default
        "/usr/local/bin/stockfish",  # Intel Mac default
        "/opt/local/bin/stockfish",  # MacPorts location
        os.path.expanduser("~/homebrew/bin/stockfish"),  # User Homebrew
        "/usr/bin/stockfish",  # Uncommon but possible
        "/usr/games/stockfish",  # Linux default
    ]

    # Check for common stockfish binary variations
    binary_names = [
        "stockfish",
        "stockfish-16",
        "stockfish-15",
        "stockfish-14",
    ]

    # Print current working directory and PATH for debugging
    print(f"\nDEBUG: Current working directory: {os.getcwd()}")
    print(f"DEBUG: PATH environment: {os.environ.get('PATH', '')}")

    # Try to find stockfish executable
    if os.name == "darwin" or os.name == "posix":
        # First try using 'which' to find where stockfish is actually installed
        for binary in binary_names:
            try:
                result = subprocess.run(
                    ["which", binary],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0 and result.stdout.strip():
                    filepath = result.stdout.strip()

                    if os.path.exists(filepath) and os.access(
                        filepath, os.X_OK
                    ):
                        print(f"DEBUG: Found Stockfish at {filepath}")
                        return filepath

            except Exception as e:
                print(f"DEBUG: Error running 'which {binary}': {e}")

        # Try the predefined paths
        for path in macos_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                print(f"DEBUG: Found Stockfish at {path}")
                return path

        # Check homebrew alternative locations
        try:
            # Get homebrew prefix
            result = subprocess.run(
                ["brew", "--prefix"],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                brew_prefix = result.stdout.strip()
                brew_path = os.path.join(brew_prefix, "bin", "stockfish")

                if os.path.exists(brew_path) and os.access(brew_path, os.X_OK):
                    print(f"DEBUG: Found Stockfish at {brew_path}")
                    return brew_path

        except Exception as e:
            print(f"DEBUG: Error checking brew prefix: {e}")

    else:
        filepath = "/usr/games/stockfish"  # Linux default path

        if os.path.exists(filepath) and os.access(filepath, os.X_OK):
            return filepath

    # No engine found, skip the test with detailed information
    debug_info = "\n".join(
        [
            f"Checked binary names: {binary_names}",
            f"Checked paths: {macos_paths}",
            f"PATH environment: {os.environ.get('PATH', '')}",
            "Try running 'which stockfish' in your terminal to locate it",
        ]
    )
    pytest.skip(f"Stockfish engine not found. {debug_info}")
