from __future__ import annotations

import contextlib
import io
import os
import unittest.mock

import chess
import pytest

import src.game_logic


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


def test_evaluate_and_show_moves_timing(
    new_board: chess.Board, engine_path: str
) -> None:
    """Test that evaluate_and_show_moves returns timing information."""
    pytest.importorskip("chess.engine")

    if not os.path.exists(engine_path):
        pytest.skip("Engine not found")

    with pytest.MonkeyPatch.context() as mp:
        # Replace get_move_evals with a simple function that returns dummy data
        def mock_get_evals(
            *args: object, **kwargs: object
        ) -> dict[chess.Move, tuple[int, int | None]]:
            return {chess.Move.from_uci("e2e4"): (100, None)}

        mp.setattr("src.engine_handler.get_move_evals", mock_get_evals)

        # Mock the display_progress function to avoid terminal output
        def mock_display_progress(*args: object, **kwargs: object) -> None:
            pass

        mp.setattr("src.board_ui.display_progress", mock_display_progress)

        # Mock the print functions to capture output
        def mock_print_tablebase_info(*args: object, **kwargs: object) -> None:
            pass

        def mock_print_possible_moves(*args: object, **kwargs: object) -> None:
            pass

        def mock_show_mate_info(*args: object, **kwargs: object) -> None:
            pass

        mp.setattr(
            "src.board_ui.print_tablebase_info", mock_print_tablebase_info
        )
        mp.setattr(
            "src.board_ui.print_possible_moves", mock_print_possible_moves
        )
        mp.setattr("src.board_ui.show_mate_info", mock_show_mate_info)

        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            moves_eval, eval_time = src.game_logic.evaluate_and_show_moves(
                new_board, None  # type: ignore
            )
            output = buf.getvalue()

        assert isinstance(eval_time, float)
        assert eval_time >= 0
        assert len(moves_eval) == 1
        assert "Evaluation time:" in output


def test_evaluate_and_show_moves_uses_dynamic_depth() -> None:
    """Test that evaluate_and_show_moves uses dynamic depth instead of fixed depth."""
    board = chess.Board()
    mock_engine = unittest.mock.MagicMock()

    # Track the depth parameter passed to get_move_evals
    with unittest.mock.patch(
        "src.engine_handler.get_move_evals"
    ) as mock_get_evals:
        mock_get_evals.return_value = {
            chess.Move.from_uci("e2e4"): (100, None)
        }

        # Mock the UI functions
        with unittest.mock.patch(
            "src.board_ui.print_tablebase_info"
        ), unittest.mock.patch(
            "src.board_ui.print_possible_moves"
        ), unittest.mock.patch(
            "src.board_ui.show_mate_info"
        ):

            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                src.game_logic.evaluate_and_show_moves(board, mock_engine)

        # Verify get_move_evals was called with dynamic depth
        mock_get_evals.assert_called_once()
        call_args = mock_get_evals.call_args

        # The depth should be the dynamic depth for starting position (14)
        assert call_args.kwargs["depth"] == 14
