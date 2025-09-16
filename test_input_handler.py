from contextlib import redirect_stdout
from io import StringIO

import pytest
from chess import Board, Move

from input_handler import from_uci, parse_move_input


def test_from_uci_valid():
    move = from_uci("e2e4")
    assert move == Move.from_uci("e2e4")


def test_from_uci_invalid():
    with pytest.raises(ValueError):
        from_uci("invalid")


def test_parse_move_input_san():
    board = Board()

    # Test SAN parsing
    result = parse_move_input(board, "e4")
    expected = Move.from_uci("e2e4")
    assert result == expected


def test_parse_move_input_uci():
    board = Board()

    # Test UCI parsing
    result = parse_move_input(board, "e2e4")
    expected = Move.from_uci("e2e4")
    assert result == expected


def test_parse_move_input_invalid():
    board = Board()

    result = parse_move_input(board, "invalid")
    assert result is None


@pytest.fixture
def new_board():
    return Board()

    with StringIO() as buf, redirect_stdout(buf):
        move = handle_user_input(new_board)

def test_handle_user_input_valid_move(monkeypatch):
    """Test handle_user_input with valid input."""
    from input_handler import handle_user_input

    board = Board()

    # Mock the input function to return a valid move
    monkeypatch.setattr("builtins.input", lambda _: "e4")

    with StringIO() as buf, redirect_stdout(buf):
        move = handle_user_input(board)

    assert move == Move.from_uci("e2e4")


def test_handle_user_input_illegal_move(monkeypatch):
    """Test handle_user_input with an illegal move."""
    from input_handler import handle_user_input

    # Set up a board where e4 is no longer legal
    board = Board()
    board.push(Move.from_uci("e2e4"))  # Already moved the e-pawn

    # Mock the input function to return e4 again (which is now illegal)
    monkeypatch.setattr("builtins.input", lambda _: "e4")

    with StringIO() as buf, redirect_stdout(buf):
        move = handle_user_input(board)
        output = buf.getvalue()  # Get the value BEFORE exiting the context
        assert "Illegal move" in output

    assert move is None
