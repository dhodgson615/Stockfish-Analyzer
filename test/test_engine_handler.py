from __future__ import annotations

import contextlib
import io
import os
import unittest.mock

import chess
import chess.engine
import pytest

import src.engine_handler
import src.input_handler

STOCKFISH_PATH = "/opt/homebrew/bin/stockfish"
PATH_NOT_FOUND = not os.path.exists(STOCKFISH_PATH)
PATH_NOT_FOUND_MSG = "Stockfish engine not found"


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_get_engine(engine_path: str) -> None:
    """Test that the engine can be initialized and quit properly."""
    engine = src.engine_handler.get_engine(engine_path)

    try:
        assert engine is not None

        board = chess.Board()
        result = engine.play(board, chess.engine.Limit(time=0.1))

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
    engine = src.engine_handler.get_engine(engine_path)

    try:
        board = chess.Board()
        move = src.input_handler.from_uci("e2e4")

        result_move, (score, mate) = src.engine_handler.evaluate_move(
            board, engine, move, depth=10
        )

        assert result_move == move
        assert isinstance(score, int)
        assert abs(score) < 10000

    finally:
        engine.quit()


def get_limited_evals(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    moves: list[chess.Move],
    depth: int = 5,
) -> dict[chess.Move, tuple[int | None, int | None]]:
    """Get evaluations for a limited set of moves."""
    moves_evaluations = {}

    for move in moves:
        move_obj, score_data = src.engine_handler.evaluate_move(
            board, engine, move, depth
        )
        moves_evaluations[move_obj] = score_data

    return moves_evaluations


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_get_move_evals_simple_position(engine_path: str) -> None:
    """Test that get_move_evals returns evaluations for all legal
    moves.
    """
    engine = src.engine_handler.get_engine(engine_path)

    try:
        board = chess.Board()
        moves = [move for move in list(board.legal_moves)[:2]]
        evals = get_limited_evals(board, engine, moves)

        assert len(evals) == len(moves)

        for move in moves:
            score, mate = evals[move]

            assert move in evals
            assert isinstance(score, int)

    finally:
        engine.quit()


def test_get_syzygy_tablebase_nonexistent_path() -> None:
    """Test that get_syzygy_tablebase() handles nonexistent paths"""
    with unittest.mock.patch("os.path.exists", return_value=False):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            tablebase = src.engine_handler.get_syzygy_tablebase(
                "/nonexistent/path"
            )
            output = buf.getvalue()

        assert tablebase is None
        assert "not found" in output


def test_get_syzygy_tablebase_exception() -> None:
    """Test that get_syzygy_tablebase() handles exceptions
    gracefully.
    """
    with patch("os.path.exists", return_value=True), patch(
        "src.engine_handler.open_tablebase",
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
        with raises((FileNotFoundError, OSError)):
            get_engine("/nonexistent/engine/path")


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


@patch("src.engine_handler.SimpleEngine")
def test_popen_uci_success(mock_simple_engine_class: MagicMock) -> None:
    """Test successful engine opening."""
    mock_engine = MagicMock()
    mock_simple_engine_class.popen_uci.return_value = mock_engine
    result = popen_uci("dummy/path")

    assert result is not None

    mock_simple_engine_class.popen_uci.assert_called_once_with("dummy/path")


@patch("src.engine_handler.SimpleEngine")
def test_popen_uci_file_not_found(mock_simple_engine_class: MagicMock) -> None:
    """Test FileNotFoundError handling in popen_uci."""
    mock_simple_engine_class.popen_uci.side_effect = FileNotFoundError(
        "No file"
    )

    with raises(FileNotFoundError):
        popen_uci("nonexistent/path")


@patch("src.engine_handler.SimpleEngine")
def test_popen_uci_general_exception(
    mock_simple_engine_class: MagicMock,
) -> None:
    """Test general exception handling in popen_uci."""
    # Create a separate mock for the popen_uci method
    mock_popen_uci = MagicMock()
    mock_popen_uci.side_effect = RuntimeError("Engine error")

    # Set the mocked method on the class
    mock_simple_engine_class.popen_uci = mock_popen_uci

    with raises(RuntimeError):
        popen_uci("problem/path")


def test_get_move_evals_with_mock() -> None:
    """Test get_move_evals using mocks to avoid actual engine use."""
    board = Board()
    mock_engine = MagicMock(spec=SimpleEngine)

    # Create a mock evaluate_move function
    with patch("src.engine_handler.evaluate_move") as mock_evaluate:
        # Configure the mock to return different values for different moves
        def side_effect(
            board: Board,
            engine: SimpleEngine,
            move: Move,
            *args: object,
            **kwargs: object,
        ) -> tuple[Move, tuple[int, int | None]]:
            return move, (100, None)

        mock_evaluate.side_effect = side_effect

        # Test the function
        with patch(
            "src.engine_handler.display_progress"
        ):  # Avoid terminal output
            result = get_move_evals(board, mock_engine)

        # Verify we have evaluations for all legal moves
        assert len(result) == len(list(board.legal_moves))
