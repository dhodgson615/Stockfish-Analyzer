import chess
import pytest

import src.engine_handler


def test_tablebase_functionality() -> None:
    """Test basic functionality of Syzygy tablebase integration."""
    tablebase = src.engine_handler.get_syzygy_tablebase()

    if not tablebase:
        pytest.skip("Tablebase not found or loaded. Check installation.")

    try:
        board = Board("8/8/8/8/8/2k5/8/K3q3 w - - 0 1")
        wdl = tablebase.get_wdl(board)

        if wdl is None:
            board = Board("8/8/8/8/8/2k5/8/K7 w - - 0 1")
            wdl = tablebase.get_wdl(board)

        assert wdl is not None, "WDL value should not be None"
        assert isinstance(wdl, int), "WDL should be an integer"

        engine = get_engine()

        try:
            moves = list(board.legal_moves)

            if not moves:
                return

            move = moves[0]

            move_obj, (_, mate) = evaluate_move(
                board, engine, move, tablebase=tablebase
            )

            assert move_obj is not None, "Move should not be None"

        finally:
            engine.quit()

    finally:
        tablebase.close()
