from __future__ import annotations

import contextlib
import io
import os

import chess
import chess.engine
import pytest

"""TODO: Consider removing this because there is no point in running
tests without the engine"""


@pytest.mark.skipif(
    not os.path.exists("/opt/homebrew/bin/stockfish"),
    reason="Stockfish engine not found",
)
def test_main_integration_with_engine_check() -> None:
    """Test that the engine can be initialized and quit properly"""
    try:
        engine = chess.engine.SimpleEngine.popen_uci(
            "/opt/homebrew/bin/stockfish"
        )

        assert engine is not None

        engine.quit()

    except Exception as e:
        pytest.fail(f"Engine initialization failed: {e}")


def test_game_integration_with_predetermined_moves(engine_path: str) -> None:
    """Test integration with a controlled game sequence."""
    pytest.importorskip("chess.engine")

    if not os.path.exists(engine_path):
        pytest.skip("Stockfish engine not found. Checked binary paths")

    # Start with a position near checkmate to keep the test short
    board = chess.Board(
        "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    )

    move_history: list[chess.Move] = []

    # Simulate a very short game by making just a few moves directly
    test_moves = [
        chess.Move.from_uci("f1c4"),  # Bishop to c4
        chess.Move.from_uci("d7d6"),  # Pawn to d6
    ]
    
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    
    try:
        # Test individual components that would be used in the game
        for move in test_moves:
            if move in board.legal_moves:
                board.push(move)
                move_history.append(move)
                
                # Test that we can evaluate the position (with very low depth for speed)
                if not board.is_game_over():
                    # Create a config with very low depth for fast testing
                    import src.config
                    test_config = src.config.EngineConfig(eval_depth=1)
                    
                    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                        moves_eval, eval_time = src.game_logic.evaluate_and_show_moves(
                            board, engine, app_config=test_config
                        )
                    
                    # Verify evaluation returns sensible results
                    assert isinstance(moves_eval, dict)
                    assert isinstance(eval_time, float)
                    assert eval_time >= 0
                    
    finally:
        engine.quit()
    
    # Verify the integration worked
    assert len(move_history) > 0
