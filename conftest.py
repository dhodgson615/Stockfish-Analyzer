import os

import pytest
from chess import Board, Move


@pytest.fixture
def new_board() -> Board:
    """Returns a fresh chess board in the starting position."""
    return Board()


@pytest.fixture
def checkmate_board() -> Board:
    """Returns a board with a checkmate position (fool's mate)."""
    board = Board()
    for move_uci in ["f2f3", "e7e5", "g2g4", "d8h4"]:
        board.push(Move.from_uci(move_uci))
    return board


@pytest.fixture
def stalemate_board() -> Board:
    """Returns a board with a stalemate position."""
    board = Board("8/8/8/8/8/5k2/7p/7K w - - 0 1")
    return board


@pytest.fixture
def sample_moves() -> list[Move]:
    """Returns a list of sample chess moves."""
    return [Move.from_uci(m) for m in ["e2e4", "d2d4", "g1f3"]]


@pytest.fixture
def engine_path() -> str:
    """Returns path to Stockfish engine, skip tests if not found."""
    path = "/opt/homebrew/bin/stockfish"
    if not os.path.exists(
        path
    ):  # Fixed: Use os.path.exists instead of path.exists
        pytest.skip("Stockfish engine not found. Skipping tests.")
    return path
