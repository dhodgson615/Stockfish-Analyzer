from contextlib import redirect_stdout
from io import StringIO
from time import time
from unittest.mock import MagicMock

import pytest
from chess import Board, Move

from board_ui import (display_progress, print_board, print_game_over_info,
                      print_game_result, print_move_history,
                      print_possible_moves, print_tablebase_info,
                      show_mate_info)
from input_handler import from_uci


def test_print_game_result_checkmate_black_wins(checkmate_board) -> None:
    # The checkmate_board fixture has White checkmated (Black wins)
    with StringIO() as buf, redirect_stdout(buf):
        print_game_result(checkmate_board)
        output = buf.getvalue()
        assert "Checkmate! Winner: Black" in output


def test_print_game_result_stalemate() -> None:
    # Create a verified stalemate position
    board = Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")

    # Verify the board is indeed in stalemate
    assert not board.is_check()
    assert board.is_stalemate()

    with StringIO() as buf, redirect_stdout(buf):
        print_game_result(board)
        output = buf.getvalue()
        assert "Stalemate! The game is a draw." in output


def test_print_game_result_insufficient_material() -> None:
    # Create a position with insufficient material
    board = Board("8/8/8/8/8/8/k7/K7 w - - 0 1")

    assert board.is_insufficient_material()

    with StringIO() as buf, redirect_stdout(buf):
        print_game_result(board)
        output = buf.getvalue()
        assert "Insufficient material" in output


def test_display_progress() -> None:
    start_time = time() - 10  # 10 seconds ago

    with StringIO() as buf, redirect_stdout(buf):
        display_progress(5, 10, start_time, 20)
        output = buf.getvalue()

        assert "[##########----------]" in output
        assert "50.0%" in output
        # Remaining time is approximately 10 seconds
        assert "00:" in output


def test_show_mate_info() -> None:
    # Create a real move and score data
    move = from_uci("e2e4")
    best_move_data = (move, (100, 3))  # Score 100, mate in 3

    with StringIO() as buf, redirect_stdout(buf):
        show_mate_info(best_move_data, True)  # White's turn
        assert "Mate in 3" in buf.getvalue()

    # Test with no mate
    best_move_data = (move, (100, None))
    with StringIO() as buf, redirect_stdout(buf):
        show_mate_info(best_move_data, True)
        assert buf.getvalue() == ""


def test_print_game_over_info(checkmate_board) -> None:
    move_history = [Move.from_uci(m) for m in ["f2f3", "e7e5", "g2g4", "d8h4"]]

    with StringIO() as buf, redirect_stdout(buf):
        print_game_over_info(checkmate_board, move_history)
        output = buf.getvalue()

        assert "Game Over!" in output
        assert "Checkmate! Winner: Black" in output
        assert "1. f2f3" in output
        assert "4. d8h4" in output


def test_print_move_history() -> None:
    moves = [Move.from_uci(m) for m in ["e2e4", "e7e5", "g1f3"]]

    with StringIO() as buf, redirect_stdout(buf):
        print_move_history(moves)
        output = buf.getvalue()
        assert "1. e2e4" in output
        assert "2. e7e5" in output
        assert "3. g1f3" in output


def test_print_possible_moves() -> None:
    # Create sorted move list with evaluation data
    moves = [
        (Move.from_uci("e2e4"), (42, None)),
        (Move.from_uci("d2d4"), (35, None)),
        (Move.from_uci("g1f3"), (30, 2)),  # This one has a mate value
    ]

    with StringIO() as buf, redirect_stdout(buf):
        print_possible_moves(moves)
        output = buf.getvalue()
        assert "e2e4" in output
        assert "Eval score: 42" in output
        assert "Eval score: 30, Mate in 2" in output


def test_print_board() -> None:
    """Test that print_board correctly formats and displays a chess
    board.
    """
    board = Board()

    with StringIO() as buf, redirect_stdout(buf):
        print_board(board)
        output = buf.getvalue()

    # Check for key elements that should be in the board output
    assert "\033c" in output  # Clear terminal command
    assert (
        "♖" in output or "R" in output
    )  # Rook character (depends on encoding)
    assert "♙" in output or "P" in output  # Pawn character
    assert "♔" in output or "K" in output  # King character
    assert "8" in output  # Board coordinate
    assert "1" in output  # Board coordinate


def test_print_tablebase_info_win() -> None:
    """Test tablebase info printing for a winning position."""
    board = Board(
        "8/8/8/8/8/2k5/8/K3q3 w - - 0 1"
    )  # White to move, losing position

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = -2  # Loss for white
    mock_tablebase.get_dtz.return_value = 10

    with StringIO() as buf, redirect_stdout(buf):
        print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

    assert "Loss" in output
    assert "DTZ: 10" in output


def test_print_tablebase_info_draw() -> None:
    """Test tablebase info printing for a drawn position."""
    board = Board("8/8/8/8/8/2k5/8/K7 w - - 0 1")  # Just kings

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = 0  # Draw
    mock_tablebase.get_dtz.return_value = 0

    with StringIO() as buf, redirect_stdout(buf):
        print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

    assert "Draw" in output


def test_print_board() -> None:
    """Test that print_board correctly formats and displays a chess board."""
    board = Board()

    with StringIO() as buf, redirect_stdout(buf):
        print_board(board)
        output = buf.getvalue()

    # Check for key elements that should be in the board output
    assert "\033c" in output  # Clear terminal command
    assert "8" in output  # Board coordinate
    assert "1" in output  # Board coordinate
    # Check for at least one piece character (depends on encoding)
    assert any(char in output for char in ["♖", "♙", "♔", "R", "P", "K"])


def test_print_tablebase_info_win():
    """Test tablebase info printing for a winning position."""
    board = Board(
        "8/8/8/8/8/2k5/8/K3q3 w - - 0 1"
    )  # White to move, losing position

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = -2  # Loss for white
    mock_tablebase.get_dtz.return_value = 10

    with StringIO() as buf, redirect_stdout(buf):
        print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

    assert "Loss" in output
    assert "DTZ: 10" in output


def test_print_tablebase_info_draw():
    """Test tablebase info printing for a drawn position."""
    board = Board("8/8/8/8/8/2k5/8/K7 w - - 0 1")  # Just kings

    mock_tablebase = MagicMock()
    mock_tablebase.get_wdl.return_value = 0  # Draw
    mock_tablebase.get_dtz.return_value = 0

    with StringIO() as buf, redirect_stdout(buf):
        print_tablebase_info(board, mock_tablebase)
        output = buf.getvalue()

    assert "Draw" in output
