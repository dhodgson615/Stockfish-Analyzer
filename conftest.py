from os import path

import pytest
from chess import Board, Move

from input_handler import from_uci


@pytest.fixture
def new_board() -> Board:
    """Returns a fresh chess board in the starting position."""
    return Board()


@pytest.fixture
def checkmate_board() -> Board:
    """Returns a board with a checkmate position (fool's mate)."""
    board = Board()
    [board.push(from_uci(move)) for move in ["f2f3", "e7e5", "g2g4", "d8h4"]]

    return board


@pytest.fixture
def stalemate_board() -> Board:
    """Returns a board with a stalemate position."""
    return Board("8/8/8/8/8/5k2/7p/7K w - - 0 1")


@pytest.fixture
def sample_moves() -> list[Move]:
    """Returns a list of sample chess moves."""
    return [Move.from_uci(m) for m in ["e2e4", "d2d4", "g1f3"]]


@pytest.fixture
def engine_path() -> str:
    """Returns path to Stockfish engine, skip tests if not found."""
    filepath = "/opt/homebrew/bin/stockfish"
    if not path.exists(filepath):
        pytest.skip("Stockfish engine not found. Skipping tests.")

    return path
