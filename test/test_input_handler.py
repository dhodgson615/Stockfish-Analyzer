import contextlib
import io

import chess
import pytest

import src.input_handler


def test_from_uci_valid() -> None:
    move = src.input_handler.from_uci("e2e4")
    assert move == src.input_handler.from_uci("e2e4")


def test_from_uci_invalid() -> None:
    with pytest.raises(ValueError):
        src.input_handler.from_uci("invalid")


def test_parse_move_input_san() -> None:
    board = chess.Board()

    # Test SAN parsing
    result = parse_move_input(board, "e4")
    expected = Move.from_uci("e2e4")

    assert result == expected


def test_parse_move_input_uci() -> None:
    board = Board()

    # Test UCI parsing
    result = parse_move_input(board, "e2e4")
    expected = Move.from_uci("e2e4")

    assert result == expected


def test_parse_move_input_invalid() -> None:
    board = Board()
    result = parse_move_input(board, "invalid")

    assert result is None


@fixture
def new_board() -> Board:
    return Board()


def test_handle_user_input_valid_move(monkeypatch: MonkeyPatch) -> None:
    """Test handle_user_input with valid input."""
    board = Board()

    # Mock the input function to return a valid move
    monkeypatch.setattr("builtins.input", lambda _: "e4")

    with StringIO() as buf, redirect_stdout(buf):
        move = handle_user_input(board)

    assert move == from_uci("e2e4")


def test_handle_user_input_illegal_move(monkeypatch: MonkeyPatch) -> None:
    """Test handle_user_input with an illegal move."""
    # Set up a board where e2e4 is no longer legal
    board = Board()
    board.push(Move.from_uci("e2e4"))  # Already moved the e-pawn

    # Mock the input to return e2e4 again in UCI format (which is now illegal)
    monkeypatch.setattr("builtins.input", lambda _: "e2e4")

    with StringIO() as buf, redirect_stdout(buf):
        move = handle_user_input(board)
        output = buf.getvalue()

        assert "Illegal move" in output

    assert move is None
