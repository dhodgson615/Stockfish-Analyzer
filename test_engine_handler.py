from contextlib import redirect_stdout
from io import StringIO
from os import environ, path
from unittest.mock import patch

import pytest
from chess import Board, Move
from chess.engine import Limit

from engine_handler import evaluate_move, get_engine, get_syzygy_tablebase
from input_handler import from_uci


@pytest.mark.skipif(
    not path.exists("/opt/homebrew/bin/stockfish"),
    reason="Stockfish engine not found",
)
def test_get_engine(engine_path) -> None:
    """Test that the engine can be initialized and quit properly."""
    engine = get_engine(engine_path)
    try:
        assert engine is not None
        board = Board()
        result = engine.play(board, Limit(time=0.1))
        assert result.move in board.legal_moves
    finally:
        engine.quit()


@pytest.mark.skipif(
    not path.exists("/opt/homebrew/bin/stockfish"),
    reason="Stockfish engine not found",
)
def test_evaluate_move(engine_path) -> None:
    """Test evaluating a single move in the starting position."""
    engine = get_engine(engine_path)

    try:
        board = Board()
        move = from_uci("e2e4")
        result_move, (score, mate) = evaluate_move(
            board, engine, move, depth=10
        )
        assert result_move == move
        assert isinstance(score, int)
        assert abs(score) < 10000
    finally:
        engine.quit()


@pytest.mark.skipif(
    not path.exists("/opt/homebrew/bin/stockfish"),
    reason="Stockfish engine not found",
)
def test_get_move_evals_simple_position(engine_path) -> None:
    """Test evaluating a limited set of moves in a simple position."""
    engine = get_engine(engine_path)
    try:
        board = Board()
        moves = [move for move in list(board.legal_moves)[:2]]

        def get_limited_evals(
            board, engine, depth=5
        ) -> dict[
            Move, tuple[int, int | None]
        ]:  # TODO: refactor to avoid nesting
            moves_evaluations = {}

            for move in moves:
                move_obj, score_data = evaluate_move(
                    board, engine, move, depth
                )
                moves_evaluations[move_obj] = score_data

            return moves_evaluations

        evals = get_limited_evals(board, engine)
        assert len(evals) == len(moves)

        for move in moves:
            assert move in evals
            score, mate = evals[move]
            assert isinstance(score, int)

    finally:
        engine.quit()


def test_get_syzygy_tablebase_nonexistent_path() -> None:
    """Test tablebase loading with a nonexistent path."""
    with patch("os.path.exists", return_value=False):
        with StringIO() as buf, redirect_stdout(buf):
            tablebase = get_syzygy_tablebase("/nonexistent/path")
            output = buf.getvalue()
        assert tablebase is None
        assert "not found" in output


def test_get_syzygy_tablebase_exception() -> None:
    """Test tablebase loading with an exception during
    initialization.
    """
    with patch("os.path.exists", return_value=True), patch(
        "engine_handler.open_tablebase",
        side_effect=Exception("Test exception"),
    ):
        with StringIO() as buf, redirect_stdout(buf):
            tablebase = get_syzygy_tablebase()
            output = buf.getvalue()
        assert tablebase is None
        assert "Error loading" in output


def test_get_engine_invalid_path() -> None:
    """Test engine initialization with an invalid engine path."""
    if not environ.get("CI"):
        with pytest.raises((FileNotFoundError, IOError)):
            engine = get_engine("/nonexistent/engine/path")
