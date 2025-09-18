from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from os import environ, path
from unittest.mock import MagicMock, patch

import pytest
from chess import Board, Move
from chess.engine import Limit, SimpleEngine

from engine_handler import (EVAL_DEPTH, evaluate_move, get_engine,
                            get_engine_evaluation, get_move_evals,
                            get_syzygy_tablebase, popen_uci,
                            try_tablebase_evaluation)
from input_handler import from_uci

STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"
PATH_NOT_FOUND = not path.exists(STOCKFISH_PATH)
PATH_NOT_FOUND_MSG = "Stockfish engine not found"


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_get_engine(engine_path) -> None:
    """Test that the engine can be initialized and quit properly."""
    engine = get_engine(engine_path)

    try:
        assert engine is not None
        board = Board()
        result = engine.play(board, Limit(time=0.1))
        # Check if result.move is not None before using 'in' operator
        if result.move is not None:
            assert result.move in board.legal_moves
        else:
            pytest.fail("Engine did not return a move")

    finally:
        engine.quit()


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_evaluate_move(engine_path: str) -> None:
    """Test that evaluate_move returns a move and score."""
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


def get_limited_evals(
    board: Board, engine: SimpleEngine, moves: list[Move], depth: int = 5
) -> dict[Move, tuple[int | None, int | None]]:
    """Get evaluations for a limited set of moves."""
    moves_evaluations = {}
    for move in moves:
        move_obj, score_data = evaluate_move(board, engine, move, depth)
        moves_evaluations[move_obj] = score_data

    return moves_evaluations


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_get_move_evals_simple_position(engine_path: str) -> None:
    """Test that get_move_evals returns evaluations for all legal
    moves.
    """
    engine = get_engine(engine_path)

    try:
        board = Board()
        moves = [move for move in list(board.legal_moves)[:2]]
        evals = get_limited_evals(board, engine, moves)
        assert len(evals) == len(moves)

        for move in moves:
            assert move in evals
            score, mate = evals[move]
            assert isinstance(score, int)

    finally:
        engine.quit()


def test_get_syzygy_tablebase_nonexistent_path() -> None:
    """Test that get_syzygy_tablebase() handles nonexistent paths"""
    with patch("os.path.exists", return_value=False):
        with StringIO() as buf, redirect_stdout(buf):
            tablebase = get_syzygy_tablebase("/nonexistent/path")
            output = buf.getvalue()

        assert tablebase is None
        assert "not found" in output


def test_get_syzygy_tablebase_exception() -> None:
    """Test that get_syzygy_tablebase() handles exceptions
    gracefully.
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
    """Test that get_engine() raises an error for an invalid path."""
    if not environ.get("CI"):
        with pytest.raises((FileNotFoundError, IOError)):
            engine = get_engine("/nonexistent/engine/path")


def test_try_tablebase_evaluation_win() -> None:
    """Test tablebase evaluation for a winning position."""
    board = Board("8/8/8/8/8/K7/8/k1q5 w - - 0 1")  # White to move, losing

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = -2  # Loss for white
    mock_tablebase.get_dtz.return_value = 5

    result = try_tablebase_evaluation(board, mock_tablebase)

    assert result is not None
    score, mate_val = result
    assert score is not None and score < -900000  # Large penalty for losing
    assert mate_val is not None and mate_val == -5  # Mate in 5


def test_try_tablebase_evaluation_none_wdl() -> None:
    """Test tablebase evaluation when wdl returns None."""
    board = Board()

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = None

    result = try_tablebase_evaluation(board, mock_tablebase)
    assert result is None


def test_try_tablebase_evaluation_exceptions() -> None:
    """Test all specific exceptions in try_tablebase_evaluation."""
    board = Board()
    mock_tablebase = MagicMock()

    # Test IOError
    mock_tablebase.get_wdl.side_effect = IOError("Test IO error")
    result = try_tablebase_evaluation(board, mock_tablebase)
    assert result is None

    # Test ValueError
    mock_tablebase.get_wdl.side_effect = ValueError("Test value error")
    result = try_tablebase_evaluation(board, mock_tablebase)
    assert result is None

    # Test IndexError
    mock_tablebase.get_wdl.side_effect = IndexError("Test index error")
    result = try_tablebase_evaluation(board, mock_tablebase)
    assert result is None


def test_get_engine_evaluation() -> None:
    """Test engine evaluation parsing."""
    board = Board()
    mock_engine = MagicMock(spec=SimpleEngine)

    # Mock a regular score
    mock_score = MagicMock()
    mock_score.white.return_value.score.return_value = 42
    mock_score.white.return_value.mate.return_value = None

    mock_engine.analyse.return_value = {"score": mock_score}

    score, mate = get_engine_evaluation(board, mock_engine, EVAL_DEPTH)
    assert score == 42
    assert mate is None

    # Mock a mate score
    mock_score.white.return_value.score.return_value = 900000
    mock_score.white.return_value.mate.return_value = 3

    mock_engine.analyse.return_value = {"score": mock_score}

    score, mate = get_engine_evaluation(board, mock_engine, EVAL_DEPTH)
    assert score == 900000
    assert mate == 3


@patch("engine_handler.SimpleEngine")
def test_popen_uci_success(mock_simple_engine_class: MagicMock) -> None:
    """Test successful engine opening."""
    mock_engine = MagicMock()
    mock_simple_engine_class.popen_uci.return_value = mock_engine

    result = popen_uci("dummy/path")
    assert result is not None
    mock_simple_engine_class.popen_uci.assert_called_once_with("dummy/path")


@patch("engine_handler.SimpleEngine")
def test_popen_uci_file_not_found(mock_simple_engine_class: MagicMock) -> None:
    """Test FileNotFoundError handling in popen_uci."""
    mock_simple_engine.popen_uci.side_effect = FileNotFoundError("No file")

    with pytest.raises(FileNotFoundError):
        popen_uci("nonexistent/path")


@patch("engine_handler.SimpleEngine")
def test_popen_uci_general_exception(
    mock_simple_engine: SimpleEngine,
) -> None:
    """Test general exception handling in popen_uci."""
    mock_simple_engine.popen_uci.side_effect = RuntimeError("Engine error")

    with pytest.raises(RuntimeError):
        popen_uci("problem/path")


def test_get_move_evals_with_mock() -> None:
    """Test get_move_evals using mocks to avoid actual engine use."""
    board = Board()
    mock_engine = MagicMock(spec=SimpleEngine)

    # Create a mock evaluate_move function
    with patch("engine_handler.evaluate_move") as mock_evaluate:
        # Configure the mock to return different values for different moves
        def side_effect(
            board, engine, move, *args, **kwargs
        ) -> tuple[Move, tuple[int, int | None]]:
            return move, (100, None)

        mock_evaluate.side_effect = side_effect

        # Test the function
        with patch("engine_handler.display_progress"):  # Avoid terminal output
            result = get_move_evals(board, mock_engine)

        # Verify we have evaluations for all legal moves
        assert len(result) == len(list(board.legal_moves))
