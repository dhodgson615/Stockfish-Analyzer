import contextlib
import io

import chess
import pytest

import src.input_handler


def test_parse_move_input_san() -> None:
    board = chess.Board()

    # Test SAN parsing
    result = src.input_handler.parse_move_input(board, "e4")
    expected = chess.Move.from_uci("e2e4")

    assert result == expected


def test_parse_move_input_uci() -> None:
    # Test UCI parsing
    board = chess.Board()
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

    assert result == expected


def test_handle_user_input_invalid_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test handle_user_input with an invalid move."""
    board = chess.Board()
    monkeypatch.setattr("builtins.input", lambda _: "invalid")

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        result = src.input_handler.handle_user_input(board)
        output = buf.getvalue()

    assert result is None
    assert "Invalid move format" in output


def test_handle_user_input_illegal_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test handle_user_input with a move that's illegal in the position."""
    board = chess.Board()

    # Use a move that parses correctly but is illegal in the starting position
    monkeypatch.setattr(
        "builtins.input", lambda _: "e2e5"
    )  # Valid format but illegal in starting position

    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        result = src.input_handler.handle_user_input(board)
        output = buf.getvalue()

    assert result is None
    assert "Illegal move" in output


def test_handle_user_input_quit_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test handle_user_input with quit command."""
    board = chess.Board()
    monkeypatch.setattr("builtins.input", lambda _: "quit")

    with pytest.raises(SystemExit):
        src.input_handler.handle_user_input(board)
