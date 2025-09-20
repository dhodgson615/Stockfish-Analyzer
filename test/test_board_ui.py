from __future__ import annotations

import contextlib
import io
import time
import unittest.mock

import chess

import src.board_ui


def test_clear_terminal() -> None:
    """Test that clear_terminal uses the correct escape sequence."""
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.clear_terminal()
        output = buf.getvalue()
        assert output == "\033c"


def test_print_board_with_clear() -> None:
    """Test print_board with CLEAR_BEFORE_PRINT enabled."""
    board = chess.Board()
    original_value = src.board_ui.CLEAR_BEFORE_PRINT
    src.board_ui.CLEAR_BEFORE_PRINT = True

    with unittest.mock.patch("src.board_ui.clear_terminal") as mock_clear:
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            src.board_ui.print_board(board)
            output = buf.getvalue()

        mock_clear.assert_called_once()
        assert "♜" in output or "♖" in output  # Verify board was printed

    # Restore original value
    src.board_ui.CLEAR_BEFORE_PRINT = original_value


def test_print_board_without_clear() -> None:
    """Test print_board with CLEAR_BEFORE_PRINT disabled."""
    board = chess.Board()
    original_value = src.board_ui.CLEAR_BEFORE_PRINT
    src.board_ui.CLEAR_BEFORE_PRINT = False

    with unittest.mock.patch("src.board_ui.clear_terminal") as mock_clear:
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            src.board_ui.print_board(board)
            output = buf.getvalue()

        mock_clear.assert_not_called()
        assert "♜" in output or "♖" in output  # Verify board was printed

    # Restore original value
    src.board_ui.CLEAR_BEFORE_PRINT = original_value


def test_display_progress_zero_iteration() -> None:
    """Test display_progress with zero iterations (edge case)."""
    start_time = time.time() - 10

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.display_progress(0, 10, start_time, 20)
        output = buf.getvalue()

        assert "[--------------------]" in output
        assert "0.0%" in output


def test_display_progress_completed() -> None:
    """Test display_progress at 100% completion."""
    start_time = time.time() - 10

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_game_result(board)
        output = buf.getvalue()
        assert "Stalemate! The game is a draw." in output


def test_print_game_result_insufficient_material() -> None:
    """Test print_game_result() for an insufficient material scenario."""
    # Create a position with insufficient material
    board = chess.Board("8/8/8/8/8/8/k7/K7 w - - 0 1")

    assert board.is_insufficient_material()

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_game_result(board)
        output = buf.getvalue()
        assert "Insufficient material" in output


def test_display_progress() -> None:
    """Test the display_progress function with mocked time."""
    start_time = time.time() - 10  # 10 seconds ago

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.display_progress(5, 10, start_time, 20)
        output = buf.getvalue()

        assert "[##########----------]" in output
        assert "50.0%" in output
        # Remaining time is approximately 10 seconds
        assert "00:" in output


def test_show_mate_info() -> None:
    """Test show_mate_info function."""
    # Create a real move and score data
    move = chess.Move.from_uci("e2e4")

    # Explicitly annotate the type to allow for None values
    best_move_data_with_mate: tuple[
        chess.Move, tuple[int | None, int | None]
    ] = (
        move,
        (100, 3),
    )

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.show_mate_info(
            best_move_data_with_mate, True
        )  # White's turn
        assert "Mate in 3" in buf.getvalue()

    # Test with no mate - using a new variable to avoid type confusion
    best_move_data_no_mate: tuple[
        chess.Move, tuple[int | None, int | None]
    ] = (
        move,
        (100, None),
    )

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.show_mate_info(best_move_data_no_mate, True)
        assert buf.getvalue() == ""


def test_print_game_over_info(checkmate_board: chess.Board) -> None:
    """Test print_game_over_info function."""
    move_history = [
        chess.Move.from_uci(m) for m in ["f2f3", "e7e5", "g2g4", "d8h4"]
    ]

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_game_over_info(checkmate_board, move_history)
        output = buf.getvalue()

        assert "Game Over!" in output
        assert "Checkmate! Winner: Black" in output
        assert "1. f2f3" in output
        assert "4. d8h4" in output


def test_print_move_history() -> None:
    """Test print_move_history function."""
    moves = [chess.Move.from_uci(m) for m in ["e2e4", "e7e5", "g1f3"]]

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_move_history(moves)
        output = buf.getvalue()

        assert "1. e2e4" in output
        assert "2. e7e5" in output
        assert "3. g1f3" in output


def test_print_possible_moves() -> None:
    """Test print_possible_moves function."""
    # Create move objects first
    move1 = chess.Move.from_uci("e2e4")
    move2 = chess.Move.from_uci("d2d4")
    move3 = chess.Move.from_uci("g1f3")

    # Create evaluation tuples with explicit types
    eval1: tuple[int | None, int | None] = (42, None)
    eval2: tuple[int | None, int | None] = (35, None)
    eval3: tuple[int | None, int | None] = (30, 2)

    # Combine into a properly typed list
    moves = [
        (move1, eval1),
        (move2, eval2),
        (move3, eval3),
    ]

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_possible_moves(moves)
        output = buf.getvalue()

        assert "e2e4" in output
        assert "Eval score: 42" in output
        assert "Eval score: 30, Mate in 2" in output


def test_print_board() -> None:
    """Test print_board function."""
    board = chess.Board()

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_board(board)
        output = buf.getvalue()

        # Check if the board contains chess piece Unicode characters
        assert "♜" in output or "♖" in output  # Rook
        assert "♛" in output or "♕" in output  # Queen


def test_print_tablebase_info() -> None:
    """Test print_tablebase_info function with a mock tablebase."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.return_value = 1  # Win
    mock_tablebase.get_dtz.return_value = 5  # Distance to zero

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

        assert "Tablebase: Win" in output
        assert "DTZ: 5" in output
