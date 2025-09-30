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
        assert "♜" in output or "♖" in output

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
        assert "♜" in output or "♖" in output

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
        src.board_ui.display_progress(10, 10, start_time, 20)
        output = buf.getvalue()

        assert "[####################]" in output
        assert "100.0%" in output
        assert "Remaining: 00:00" in output


def test_print_possible_moves_empty() -> None:
    """Test print_possible_moves with empty list."""
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_possible_moves([])
        output = buf.getvalue()

        assert "Possible moves:" in output
        # No moves should be listed


def test_print_possible_moves_with_none_values() -> None:
    """Test print_possible_moves with None score values."""
    move = chess.Move.from_uci("e2e4")

    moves_data: list[tuple[chess.Move, tuple[int | None, int | None]]] = [
        (move, (None, None))
    ]

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_possible_moves(moves_data)
        output = buf.getvalue()

        assert "e2e4" in output
        assert "Eval score: None" in output


def test_print_move_history_empty() -> None:
    """Test print_move_history with empty list."""
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_move_history([])
        output = buf.getvalue()

        assert "Moves played:" in output
        # No moves should be listed


def test_print_move_history_custom_moves_per_line() -> None:
    """Test print_move_history with custom moves per line."""
    moves = [
        chess.Move.from_uci(m)
        for m in ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"]
    ]

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_move_history(moves, moves_per_line=3)
        output = buf.getvalue()

        # Check if there's a newline after the 3rd move
        assert "3. g1f3\n" in output


def test_print_game_result_fifty_moves() -> None:
    """Test print_game_result for fifty-move rule."""
    board = chess.Board()
    board.halfmove_clock = 100  # Set fifty-move counter

    with unittest.mock.patch.object(
        board, "is_fifty_moves", return_value=True
    ):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            src.board_ui.print_game_result(board)
            output = buf.getvalue()

            assert "Fifty-move rule" in output


def test_print_game_result_threefold_repetition() -> None:
    """Test print_game_result for threefold repetition."""
    board = chess.Board()

    with unittest.mock.patch.object(board, "is_repetition", return_value=True):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            src.board_ui.print_game_result(board)
            output = buf.getvalue()

            assert "Threefold repetition" in output


def test_print_game_result_other() -> None:
    """Test print_game_result for other results."""
    board = chess.Board()

    with unittest.mock.patch.object(
        board, "is_checkmate", return_value=False
    ), unittest.mock.patch.object(
        board, "is_stalemate", return_value=False
    ), unittest.mock.patch.object(
        board, "is_insufficient_material", return_value=False
    ), unittest.mock.patch.object(
        board, "is_fifty_moves", return_value=False
    ), unittest.mock.patch.object(
        board, "is_repetition", return_value=False
    ), unittest.mock.patch.object(
        board, "result", return_value="1/2-1/2"
    ):
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            src.board_ui.print_game_result(board)
            output = buf.getvalue()

            assert "Game result: 1/2-1/2" in output


def test_show_mate_info_black_win() -> None:
    """Test show_mate_info for Black's mate."""
    move = chess.Move.from_uci("e7e5")
    mate_data = (move, (100, -3))  # Black mates in 3

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.show_mate_info(mate_data, False)  # Black's turn
        output = buf.getvalue()

        assert "Mate in 3" in output


def test_show_mate_info_no_mate() -> None:
    """Test show_mate_info when no mate is found."""
    move = chess.Move.from_uci("e2e4")
    no_mate_data = (move, (100, None))

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.show_mate_info(no_mate_data, True)
        output = buf.getvalue()

        assert output == ""  # No output expected


def test_show_mate_info_opponent_mate() -> None:
    """Test show_mate_info when opponent has mate (should not display)."""
    move = chess.Move.from_uci("e2e4")
    opponent_mate_data = (move, (100, -3))  # Opponent has mate in 3

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.show_mate_info(opponent_mate_data, True)  # White's turn
        output = buf.getvalue()

        assert output == ""  # No output expected


def test_print_tablebase_info_io_error() -> None:
    """Test print_tablebase_info when IOError occurs."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.side_effect = IOError("Test IO error")

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

        assert output == ""  # Should handle exception silently


def test_print_tablebase_info_value_error() -> None:
    """Test print_tablebase_info when ValueError occurs."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.side_effect = ValueError("Test value error")

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

        assert output == ""  # Should handle exception silently


def test_print_tablebase_info_index_error() -> None:
    """Test print_tablebase_info when IndexError occurs."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.side_effect = IndexError("Test index error")

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

        assert output == ""  # Should handle exception silently


def test_print_tablebase_info_none_tablebase() -> None:
    """Test print_tablebase_info with None tablebase."""
    board = chess.Board()

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, None)  # type: ignore
        output = buf.getvalue()

        assert output == ""  # Should handle None silently


def test_print_tablebase_info_draw() -> None:
    """Test print_tablebase_info for draw position."""
    board = chess.Board()
    mock_tablebase = unittest.mock.MagicMock()
    mock_tablebase.get_wdl.return_value = 0  # Draw
    mock_tablebase.get_dtz.return_value = 0

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        src.board_ui.print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

        assert "Draw" in output
        assert "DTZ: 0" in output
