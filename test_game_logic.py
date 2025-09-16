from contextlib import redirect_stdout
from io import StringIO
from os import path

import pytest
from chess import Move
from chess.engine import SimpleEngine

from game_logic import sort_moves_by_evaluation


def test_sort_moves_by_evaluation():
    # Create real moves and evaluation data
    move1 = Move.from_uci("e2e4")
    move2 = Move.from_uci("d2d4")
    move3 = Move.from_uci("c2c4")

    moves_eval = {
        move1: (100, None),
        move2: (50, None),
        move3: (75, None),
    }

    # Test sorting for both white and black
    white_sorted = sort_moves_by_evaluation(moves_eval, True)
    black_sorted = sort_moves_by_evaluation(moves_eval, False)

    assert white_sorted[0][0] == move1
    assert white_sorted[1][0] == move3
    assert white_sorted[2][0] == move2

    assert black_sorted[0][0] == move2
    assert black_sorted[1][0] == move3
    assert black_sorted[2][0] == move1


def test_evaluate_and_show_moves_timing(new_board, engine_path):
    """Test that evaluate_and_show_moves returns timing information."""
    pytest.importorskip("chess.engine")
    if not path.exists(engine_path):
        pytest.skip("Engine not found")

    from game_logic import evaluate_and_show_moves

    with pytest.MonkeyPatch.context() as mp:
        # Replace get_move_evals with a simple function that returns dummy data
        def mock_get_evals(*args, **kwargs):
            return {Move.from_uci("e2e4"): (100, None)}

        mp.setattr("game_logic.get_move_evals", mock_get_evals)

        engine = SimpleEngine.popen_uci(engine_path)
        try:
            with StringIO() as buf, redirect_stdout(buf):
                moves_eval, eval_time = evaluate_and_show_moves(
                    new_board, engine
                )

            assert isinstance(moves_eval, dict)
            assert isinstance(eval_time, float)
            assert eval_time >= 0
        finally:
            engine.quit()
