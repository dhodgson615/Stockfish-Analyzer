import os

import chess
import pytest

import src.input_handler


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
    """Returns path to Stockfish engine, skip tests if not found."""
    filepath = "/opt/homebrew/bin/stockfish"

    if not os.path.exists(filepath):
        pytest.skip("Stockfish engine not found. Skipping tests.")

    return filepath
