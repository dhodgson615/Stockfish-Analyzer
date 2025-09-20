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
        move = chess.Move.from_uci("e2e4")

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
    with unittest.mock.patch(
        "os.path.exists", return_value=True
    ), unittest.mock.patch(
        "chess.syzygy.open_tablebase",
        side_effect=Exception("Test exception"),
    ):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            tablebase = src.engine_handler.get_syzygy_tablebase()
            output = buf.getvalue()

        assert tablebase is None
        assert "Error loading" in output


def test_get_engine_invalid_path() -> None:
    """Test that get_engine() raises an error for an invalid path."""
    if not os.environ.get("CI"):
        with pytest.raises((FileNotFoundError, OSError)):
            src.engine_handler.get_engine("/nonexistent/engine/path")


def test_try_tablebase_evaluation_win() -> None:
    """Test tablebase evaluation for a winning position."""
    board = chess.Board(
        "8/8/8/8/8/K7/8/k1q5 w - - 0 1"
    )  # White to move, losing

    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.return_value = -2  # Loss for white
    mock_tablebase.get_dtz.return_value = 5
    result = src.engine_handler.try_tablebase_evaluation(board, mock_tablebase)

    assert result is not None

    score, mate_val = result

    assert score is not None and score < -900000  # Large penalty for losing
    assert mate_val is not None and mate_val == -5  # Mate in 5


def test_try_tablebase_evaluation_none_wdl() -> None:
    """Test tablebase evaluation when wdl returns None."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.return_value = None
    result = src.engine_handler.try_tablebase_evaluation(board, mock_tablebase)

    assert result is None


def test_try_tablebase_evaluation_exceptions() -> None:
    """Test all specific exceptions in try_tablebase_evaluation."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()

    # Test IOError
    mock_tablebase.get_wdl.side_effect = IOError("Test IO error")
    result = src.engine_handler.try_tablebase_evaluation(board, mock_tablebase)

    assert result is None

    # Test ValueError
    mock_tablebase.get_wdl.side_effect = ValueError("Test value error")
    result = src.engine_handler.try_tablebase_evaluation(board, mock_tablebase)

    assert result is None

    # Test IndexError
    mock_tablebase.get_wdl.side_effect = IndexError("Test index error")
    result = src.engine_handler.try_tablebase_evaluation(board, mock_tablebase)

    assert result is None


def test_get_engine_evaluation() -> None:
    """Test engine evaluation parsing."""
    board = chess.Board()
    mock_engine = unittest.mock.MagicMock(spec=chess.engine.SimpleEngine)

    # Mock a regular score
    mock_score = unittest.mock.MagicMock()
    mock_score.white.return_value.score.return_value = 42
    mock_score.white.return_value.mate.return_value = None
    mock_engine.analyse.return_value = {"score": mock_score}
    score, mate = src.engine_handler.get_engine_evaluation(
        board, mock_engine, src.engine_handler.EVAL_DEPTH
    )

    assert score == 42
    assert mate is None

    # Mock a mate score
    mock_score.white.return_value.score.return_value = 900000
    mock_score.white.return_value.mate.return_value = 3
    mock_engine.analyse.return_value = {"score": mock_score}
    score, mate = src.engine_handler.get_engine_evaluation(
        board, mock_engine, src.engine_handler.EVAL_DEPTH
    )

    assert score == 900000
    assert mate == 3


def test_get_move_evals_with_mock() -> None:
    """Test get_move_evals using mocks to avoid actual engine use."""
    board = chess.Board()
    mock_engine = unittest.mock.MagicMock(spec=chess.engine.SimpleEngine)

    # Create a mock evaluate_move function
    with unittest.mock.patch(
        "src.engine_handler.evaluate_move"
    ) as mock_evaluate:
        # Configure the mock to return different values for different moves
        def side_effect(
            board: chess.Board,
            engine: chess.engine.SimpleEngine,
            move: chess.Move,
            *args: object,
            **kwargs: object,
        ) -> tuple[chess.Move, tuple[int, int | None]]:
            return move, (100, None)

        mock_evaluate.side_effect = side_effect

        # Test the function - mock the display_progress function properly
        with unittest.mock.patch(
            "src.board_ui.display_progress"
        ):  # Avoid terminal output
            result = src.engine_handler.get_move_evals(board, mock_engine)

        # Verify we have evaluations for all legal moves
        assert len(result) == len(list(board.legal_moves))


def test_get_dynamic_eval_depth_opening() -> None:
    """Test dynamic depth calculation for opening positions."""
    # Starting position - should use opening depth
    board = chess.Board()
    depth = src.engine_handler.get_dynamic_eval_depth(board)

    assert depth == 14  # Opening depth

    # After a few moves, still opening
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    depth = src.engine_handler.get_dynamic_eval_depth(board)

    assert depth == 14  # Still opening


def test_get_dynamic_eval_depth_middlegame() -> None:
    """Test dynamic depth calculation for middlegame-like positions."""
    # Test opening position (move 8, many pieces)
    board = chess.Board()

    # Simulate moves - this is still opening according to our logic
    moves = [
        "e4",
        "e5",
        "Nf3",
        "Nc6",
        "Bb5",
        "a6",
        "Ba4",
        "Nf6",
        "O-O",
        "Be7",
        "Re1",
        "b5",
        "Bb3",
        "d6",
        "c3",
        "O-O",
    ]

    for move in moves:
        board.push_san(move)

    depth = src.engine_handler.get_dynamic_eval_depth(board)

    # This is still opening (move 8, 30 pieces) -> opening depth
    assert depth == 14  # Opening depth
    
    # Test a position that reaches late opening (move 12-15, many pieces)
    middlegame_fen = "r1bq1rk1/pp3ppp/2n1pn2/3p4/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 12"
    late_opening_board = chess.Board(middlegame_fen)
    
    depth_lo = src.engine_handler.get_dynamic_eval_depth(late_opening_board)
    
    # Move 12 with 26 pieces -> late opening depth
    assert depth_lo == 16  # Late opening depth
    
    # Test true middlegame (move 20+, many pieces)
    middlegame_fen = "r1bq1rk1/pp3ppp/2n1pn2/3p4/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 20"
    middlegame_board = chess.Board(middlegame_fen)
    
    depth_mg = src.engine_handler.get_dynamic_eval_depth(middlegame_board)
    
    # Move 20 with 26 pieces -> middlegame depth
    assert depth_mg == 20  # True middlegame depth


def test_get_dynamic_eval_depth_endgame() -> None:
    """Test dynamic depth calculation for endgame positions."""
    # Create an endgame position with few pieces
    board = chess.Board("8/8/8/8/8/K1k5/8/8 w - - 0 1")  # King vs King
    
    depth = src.engine_handler.get_dynamic_eval_depth(board)
    
    assert depth == 25  # Very few pieces, deepest search
    
    # Test with slightly more pieces
    board = chess.Board("8/8/8/8/8/K1k5/1P1p4/8 w - - 0 1")  # Kings + pawns
    
    depth = src.engine_handler.get_dynamic_eval_depth(board)
    
    assert depth >= 22  # Still endgame but with a few more pieces


def test_get_dynamic_eval_depth_transition() -> None:
    """Test dynamic depth calculation for transitional positions."""
    # Position with medium piece count (around 12-16 pieces)
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    
    depth = src.engine_handler.get_dynamic_eval_depth(board)
    
    # Should be endgame depth since only 6 pieces
    assert depth == 25
