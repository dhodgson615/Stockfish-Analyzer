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
    result = src.input_handler.parse_move_input(board, "e4")
    expected = chess.Move.from_uci("e2e4")

    assert result == expected


def test_parse_move_input_uci() -> None:
    board = chess.Board()

    # Test UCI parsing
    result = src.input_handler.parse_move_input(board, "e2e4")
    expected = chess.Move.from_uci("e2e4")

    assert result == expected


def test_parse_move_input_invalid() -> None:
    board = chess.Board()
    result = src.input_handler.parse_move_input(board, "invalid")

    assert result is None


def test_handle_user_input_valid_move(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test handle_user_input with a valid move."""
    board = chess.Board()
    monkeypatch.setattr("builtins.input", lambda _: "e4")

    result = src.input_handler.handle_user_input(board)
    expected = chess.Move.from_uci("e2e4")

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
