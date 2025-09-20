from __future__ import annotations

import contextlib
import io
import os

import chess
import pytest

import src.engine_handler
import src.game_logic
import src.input_handler

"""TODO: Consider removing this because there is no point in running
tests without the engine"""


@pytest.mark.skipif(
    not os.path.exists("/opt/homebrew/bin/stockfish"),
    reason="Stockfish engine not found",
)
def test_main_integration_with_engine_check() -> None:
    """Test that the engine can be initialized and quit properly"""
    try:
        engine = src.engine_handler.popen_uci("/opt/homebrew/bin/stockfish")

        assert engine is not None

        engine.quit()

    except Exception as e:
        pytest.fail(f"Engine initialization failed: {e}")


def test_play_game_simple_sequence(
    engine_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test play_game with a predetermined sequence of moves."""
    pytest.importorskip("chess.engine")

    if not path.exists(engine_path):
        skip("Engine not found")

    # Create a board that's close to a game end to reduce iterations
    board = Board(
        "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
    )

    move_history: list[Move] = []

    # Mock handle_user_input to return a checkmate sequence
    moves = [from_uci(m) for m in ["f1c4", "f8c5", "d1f3", "g7g6", "f3f7"]]
    move_iter = iter(moves)

    def mock_handle_input(_: Board) -> Move | None:
        try:
            return next(move_iter)

        except StopIteration:
            return None

    monkeypatch.setattr("src.game_logic.handle_user_input", mock_handle_input)

    # Skip actual move evaluation to speed up testing
    def mock_evaluate(
        *args: object,
    ) -> tuple[dict[Move, tuple[int, int | None]], float]:
        return {}, 0.0

    monkeypatch.setattr(
        "src.game_logic.evaluate_and_show_moves",
        lambda *args: ({}, 0.1),
    )

    engine = popen_uci(engine_path)

    try:
        with StringIO() as buf, redirect_stdout(buf):
            play_game(board, engine, move_history)

    finally:
        engine.quit()

    assert len(move_history) > 0
    assert board.is_game_over()
