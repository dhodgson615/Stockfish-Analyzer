import pytest
from chess import Board

from engine_handler import evaluate_move, get_engine, get_syzygy_tablebase


def test_tablebase_functionality():
    # Load tablebase
    tablebase = get_syzygy_tablebase()
    if not tablebase:
        pytest.skip("Tablebase not found or loaded. Check installation.")

    # Create a 3-piece endgame position (King vs King+Queen)
    board = Board("8/8/8/8/8/2k5/8/K3q3 w - - 0 1")

    try:
        # Get WDL and DTZ info directly from tablebase
        wdl = tablebase.get_wdl(board)
        dtz = tablebase.get_dtz(board)

        # If we can't probe this position, try a simpler one
        if wdl is None:
            board = Board("8/8/8/8/8/2k5/8/K7 w - - 0 1")  # Just kings
            wdl = tablebase.get_wdl(board)
            dtz = tablebase.get_dtz(board)

        assert wdl is not None, "WDL value should not be None"
        assert isinstance(wdl, int), "WDL should be an integer"

        # Test with engine evaluation if possible
        if wdl is not None:
            engine = get_engine()
            try:
                # Test a move evaluation using tablebase
                moves = list(board.legal_moves)
                
                if moves:  # Make sure there are legal moves
                    move = moves[0]
                    move_obj, (score, mate) = evaluate_move(
                        board, engine, move, tablebase=tablebase
                    )
                    assert move_obj is not None, "Move should not be None"

            finally:
                engine.quit()

    finally:
        tablebase.close()
