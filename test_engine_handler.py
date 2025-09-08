import os

import pytest
from chess import Board, Move
from chess.engine import Limit, SimpleEngine

from engine_handler import evaluate_move, get_engine, get_move_evals


class TestEngineHandler:
    """Tests that require the chess engine"""

    @pytest.mark.skipif(
        not os.path.exists("/opt/homebrew/bin/stockfish"),
        reason="Stockfish engine not found",
    )
    def test_get_engine(self, engine_path):
        engine = get_engine(engine_path)
        try:
            assert engine is not None
            # Test some basic engine operations
            board = Board()
            result = engine.play(board, Limit(time=0.1))
            assert result.move in board.legal_moves
        finally:
            engine.quit()

    @pytest.mark.skipif(
        not os.path.exists("/opt/homebrew/bin/stockfish"),
        reason="Stockfish engine not found",
    )
    def test_evaluate_move(self, engine_path):
        engine = get_engine(engine_path)
        try:
            board = Board()
            move = Move.from_uci("e2e4")

            result_move, (score, mate) = evaluate_move(
                board, engine, move, depth=10
            )

            assert result_move == move
            assert isinstance(score, int)  # Score should be an integer
            # We don't know the exact score value, but it should be reasonable
            assert abs(score) < 10000
        finally:
            engine.quit()

    @pytest.mark.skipif(
        not os.path.exists("/opt/homebrew/bin/stockfish"),
        reason="Stockfish engine not found",
    )
    def test_get_move_evals_simple_position(self, engine_path):
        # This test will be slow since it evaluates all moves
        # Consider running with a lower depth for testing
        engine = get_engine(engine_path)
        try:
            board = Board()
            # Limit to just 2 legal moves for testing
            moves = [move for move in list(board.legal_moves)[:2]]

            # Create a custom function to only evaluate our limited move set
            def get_limited_evals(board, engine, depth=5):
                moves_evaluations = {}
                for move in moves:
                    move_obj, score_data = evaluate_move(
                        board, engine, move, depth
                    )
                    moves_evaluations[move_obj] = score_data
                return moves_evaluations

            evals = get_limited_evals(board, engine)

            assert len(evals) == len(moves)
            for move in moves:
                assert move in evals
                score, mate = evals[move]
                assert isinstance(score, int)
        finally:
            engine.quit()
