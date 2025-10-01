from __future__ import annotations

import contextlib
import io

import chess

import src.game_logic


class FakeEngine:
    """Test double for chess engine that provides predictable results."""

    def __init__(
        self, evaluations: dict[str, tuple[int, int | None]] | None = None
    ):
        self.evaluations = evaluations or {"e2e4": (100, None)}
        self.analysis_calls: list[tuple[chess.Board, chess.engine.Limit]] = []

    def analyse(
        self, board: chess.Board, limit: chess.engine.Limit
    ) -> dict[str, FakeScore]:
        """Simulate engine analysis with fake scores."""
        # Track what was analyzed
        self.analysis_calls.append((board.copy(), limit))

        # Return a mock score based on the board state
        # For simplicity, just return a default evaluation
        return {"score": FakeScore(100, None)}


class FakeScore:
    """Test double for chess engine score."""

    def __init__(self, score: int, mate: int | None = None):
        self._score = score
        self._mate = mate

    def white(self) -> FakeScore:
        return self

    def score(self, mate_score: int = 1000000) -> int:
        return self._score

    def mate(self) -> int | None:
        return self._mate


def create_test_move_evaluations() -> dict[chess.Move, tuple[int, int | None]]:
    """Create realistic move evaluations for testing."""
    return {
        chess.Move.from_uci("e2e4"): (100, None),
        chess.Move.from_uci("d2d4"): (80, None),
        chess.Move.from_uci("g1f3"): (60, None),
    }


def test_sort_moves_by_evaluation() -> None:
    # Create real moves and evaluation data
    move1 = chess.Move.from_uci("e2e4")
    move2 = chess.Move.from_uci("d2d4")
    move3 = chess.Move.from_uci("c2c4")

    moves_eval: dict[chess.Move, tuple[int | None, int | None]] = {
        move1: (100, None),
        move2: (50, None),
        move3: (75, None),
    }

    white_sorted = src.game_logic.sort_moves_by_evaluation(moves_eval, True)
    black_sorted = src.game_logic.sort_moves_by_evaluation(moves_eval, False)

    assert white_sorted[0][0] == move1
    assert white_sorted[1][0] == move3
    assert white_sorted[2][0] == move2
    assert black_sorted[0][0] == move2
    assert black_sorted[1][0] == move3
    assert black_sorted[2][0] == move1


def test_evaluate_and_show_moves_timing_with_test_doubles() -> None:
    """Test that evaluate_and_show_moves returns timing information
    using test doubles.
    """
    board = chess.Board()
    fake_engine = FakeEngine()

    # Capture output for verification
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        moves_eval, eval_time = src.game_logic.evaluate_and_show_moves(
            board, fake_engine
        )

        output = buf.getvalue()

    assert isinstance(
        eval_time, float
    )  # Verify timing information is returned
    assert eval_time >= 0
    assert isinstance(moves_eval, dict)  # Verify the evaluation was performed
    assert "Evaluation time:" in output  # Verify that timing output is printed


def test_dynamic_depth_integration_with_game_logic() -> None:
    """Test that the dynamic depth calculation integrates correctly
    with game logic.
    """
    # Test the dynamic depth calculation directly with different board states
    import src.engine_handler

    # Starting position should use opening depth
    starting_board = chess.Board()
    opening_depth = src.engine_handler.get_dynamic_eval_depth(starting_board)
    assert opening_depth == 14  # Expected opening depth

    # Endgame position should use deeper search
    endgame_board = chess.Board("8/8/8/8/8/K1k5/8/8 w - - 0 1")
    endgame_depth = src.engine_handler.get_dynamic_eval_depth(endgame_board)
    assert endgame_depth == 25  # Expected endgame depth

    # The depths should be different, showing the dynamic calculation works
    assert opening_depth != endgame_depth


def test_evaluate_and_show_moves_basic_functionality() -> None:
    """Test the basic functionality of evaluate_and_show_moves with
    realistic test doubles.
    """
    board = chess.Board()
    fake_engine = FakeEngine()

    # Test without tablebase first
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        moves_eval, eval_time = src.game_logic.evaluate_and_show_moves(
            board, fake_engine
        )
        output = buf.getvalue()

    # Basic functionality verification
    assert isinstance(moves_eval, dict)
    assert isinstance(eval_time, float)
    assert eval_time >= 0
    assert "Evaluation time:" in output
