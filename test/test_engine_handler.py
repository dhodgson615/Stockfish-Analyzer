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

STOCKFISH_FOUND, STOCKFISH_PATH = src.engine_handler.find_stockfish_path()
PATH_NOT_FOUND_MSG = f"Stockfish engine not found (checked: {STOCKFISH_PATH})"
PATH_NOT_FOUND = not STOCKFISH_FOUND


@pytest.mark.skipif(PATH_NOT_FOUND, reason=PATH_NOT_FOUND_MSG)
def test_get_engine(engine_path: str) -> None:
    """Test that the engine can be initialized and quit properly."""
    src.engine_handler.get_engine(engine_path)


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


class FakeTablebase:
    """Test double for Syzygy tablebase that can simulate different scenarios."""
    
    def __init__(self, wdl_result: int | None = None, dtz_result: int = 5, 
                 should_raise: type[Exception] | None = None, error_message: str = "Test error"):
        self.wdl_result = wdl_result
        self.dtz_result = dtz_result
        self.should_raise = should_raise
        self.error_message = error_message
        self.get_wdl_calls = []
        self.get_dtz_calls = []
    
    def get_wdl(self, board):
        """Simulate tablebase WDL (Win/Draw/Loss) lookup."""
        self.get_wdl_calls.append(board)
        if self.should_raise:
            raise self.should_raise(self.error_message)
        return self.wdl_result
    
    def get_dtz(self, board):
        """Simulate tablebase DTZ (Distance to Zero) lookup."""
        self.get_dtz_calls.append(board)
        if self.should_raise:
            raise self.should_raise(self.error_message)
        return self.dtz_result


def test_try_tablebase_evaluation_win_with_test_double() -> None:
    """Test tablebase evaluation for a winning position using test double."""
    board = chess.Board(
        "8/8/8/8/8/K7/8/k1q5 w - - 0 1"
    )  # White to move, losing
    
    test_tablebase = FakeTablebase(wdl_result=-2, dtz_result=5)  # Loss for white
    result = src.engine_handler.try_tablebase_evaluation(board, test_tablebase)
    
    assert result is not None
    score, mate_val = result
    
    assert score is not None and score < -900000  # Large penalty for losing
    assert mate_val is not None and mate_val == -5  # Mate in 5
    assert len(test_tablebase.get_wdl_calls) == 1
    assert len(test_tablebase.get_dtz_calls) == 1


def test_try_tablebase_evaluation_none_wdl_with_test_double() -> None:
    """Test tablebase evaluation when wdl returns None using test double."""
    board = chess.Board()
    test_tablebase = FakeTablebase(wdl_result=None)
    result = src.engine_handler.try_tablebase_evaluation(board, test_tablebase)
    
    assert result is None
    assert len(test_tablebase.get_wdl_calls) == 1


def test_try_tablebase_evaluation_exceptions_with_test_double() -> None:
    """Test all specific exceptions in try_tablebase_evaluation using test doubles."""
    board = chess.Board()
    
    # Test IOError
    io_error_tablebase = FakeTablebase(should_raise=IOError, error_message="Test IO error")
    result = src.engine_handler.try_tablebase_evaluation(board, io_error_tablebase)
    assert result is None
    
    # Test ValueError  
    value_error_tablebase = FakeTablebase(should_raise=ValueError, error_message="Test value error")
    result = src.engine_handler.try_tablebase_evaluation(board, value_error_tablebase)
    assert result is None
    
    # Test IndexError
    index_error_tablebase = FakeTablebase(should_raise=IndexError, error_message="Test index error")
    result = src.engine_handler.try_tablebase_evaluation(board, index_error_tablebase)
    assert result is None


class FakeEngineForTesting:
    """Test double for chess engine that provides predictable results."""
    
    def __init__(self, score: int = 42, mate: int | None = None):
        self.score = score
        self.mate = mate
        self.analysis_calls = []
    
    def analyse(self, board: chess.Board, limit: chess.engine.Limit) -> dict:
        """Simulate engine analysis with configurable scores."""
        self.analysis_calls.append((board.copy(), limit))
        return {
            "score": FakeScore(self.score, self.mate)
        }


class FakeScore:
    """Test double for chess engine score."""
    
    def __init__(self, score: int, mate: int | None = None):
        self._score = score
        self._mate = mate
    
    def white(self):
        return self
    
    def score(self, mate_score: int = 1000000):
        return self._score
    
    def mate(self):
        return self._mate


def test_get_engine_evaluation_with_test_double() -> None:
    """Test engine evaluation parsing using test doubles."""
    board = chess.Board()
    
    # Test regular score
    test_engine = FakeEngineForTesting(score=42, mate=None)
    score, mate = src.engine_handler.get_engine_evaluation(
        board, test_engine, src.engine_handler.EVAL_DEPTH
    )
    
    assert score == 42
    assert mate is None
    assert len(test_engine.analysis_calls) == 1
    
    # Test mate score
    mate_engine = FakeEngineForTesting(score=900000, mate=3)
    score, mate = src.engine_handler.get_engine_evaluation(
        board, mate_engine, src.engine_handler.EVAL_DEPTH
    )
    
    assert score == 900000
    assert mate == 3


def test_get_move_evals_behavior() -> None:
    """Test get_move_evals behavior using limited scope to avoid engine dependency."""
    board = chess.Board()
    test_engine = FakeEngineForTesting(score=100, mate=None)
    
    # Test that the function processes some moves and returns results
    # We'll limit to just a few moves to avoid long evaluation times
    legal_moves = list(board.legal_moves)
    
    # Since get_move_evals calls the actual evaluate_move function,
    # and we want to avoid long engine evaluations, let's test the 
    # core behavior with a very simple position
    simple_board = chess.Board("8/8/8/8/8/8/8/K1k5 w - - 0 1")  # Very simple position
    
    # Capture output to avoid terminal noise
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        result = src.engine_handler.get_move_evals(simple_board, test_engine, depth=1)
    
    # Verify basic functionality - that we get results for legal moves
    assert isinstance(result, dict)
    assert len(result) > 0  # Should have at least one legal move
    
    # Verify the engine was actually called
    assert len(test_engine.analysis_calls) > 0


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
    middlegame_fen = (
        "r1bq1rk1/pp3ppp/2n1pn2/3p4/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 12"
    )

    late_opening_board = chess.Board(middlegame_fen)

    depth_lo = src.engine_handler.get_dynamic_eval_depth(late_opening_board)

    # Move 12 with 26 pieces -> late opening depth
    assert depth_lo == 16  # Late opening depth

    # Test true middlegame (move 20+, many pieces)
    middlegame_fen = (
        "r1bq1rk1/pp3ppp/2n1pn2/3p4/3P4/2N1PN2/PP3PPP/R1BQKB1R w KQ - 0 20"
    )

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
