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

    if not os.path.exists(filepath):
        pytest.skip("Stockfish engine not found. Skipping tests.")

    return filepath
