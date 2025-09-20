from __future__ import annotations

import time

import chess.engine
import chess.syzygy

try:
    import board_ui
    import engine_handler
    import input_handler

except ImportError:
    import src.board_ui as board_ui
    import src.engine_handler as engine_handler
    import src.input_handler as input_handler


def get_move_score(
    item: tuple[chess.Move, tuple[int | None, int | None]],
) -> int:
    """Key function for sorting moves. Takes (Move, (score,
    mate_value)) and returns score for sorting.
    """
    return item[1][0] if item[1][0] is not None else 0


def sort_moves_by_evaluation(
    moves_eval: dict[chess.Move, tuple[int | None, int | None]],
    is_white_turn: bool,
) -> list[tuple[chess.Move, tuple[int | None, int | None]]]:
    """Sorts the evaluated moves based on the score. Higher scores are
    better for White, lower scores are better for Black. Returns a list
    of tuples (Move, (score, mate_value)).
    """
    return sorted(
        list(moves_eval.items()), key=get_move_score, reverse=is_white_turn
    )


def evaluate_and_show_moves(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    tablebase: chess.syzygy.Tablebase | None = None,
) -> tuple[dict[chess.Move, tuple[int | None, int | None]], float]:
    """Evaluate moves and display them with timing information. Returns
    a tuple containing the moves evaluation dictionary and the time
    taken for the evaluation.
    """
    start_time = time.time()

    if tablebase:
        board_ui.print_tablebase_info(board, tablebase)

    moves_eval = engine_handler.get_move_evals(
        board,
        engine,
        depth=engine_handler.get_dynamic_eval_depth(board),
        tablebase=tablebase,
    )

    eval_time = time.time() - start_time
    sorted_moves = sort_moves_by_evaluation(moves_eval, board.turn)
    board_ui.print_possible_moves(sorted_moves)

    if sorted_moves:
        board_ui.show_mate_info(sorted_moves[0], board.turn)

    print(f"\nEvaluation time: {eval_time:.2f} sec\n")

    return moves_eval, eval_time


def play_game(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    move_history: list[chess.Move],
    tablebase: chess.syzygy.Tablebase | None = None,
) -> None:
    """Run the interactive chess game loop. Continues until the game is
    over. Displays the board, evaluates moves, and handles user input
    for moves.
    """
    while not board.is_game_over():
        board_ui.print_board(board)
        evaluate_and_show_moves(board, engine, tablebase)
        move = input_handler.handle_user_input(board)

        if not move:
            continue

        board.push(move)
        move_history.append(move)
