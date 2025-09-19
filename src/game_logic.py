from __future__ import annotations

from time import time

from chess import Board, Move
from chess.engine import SimpleEngine
from chess.syzygy import Tablebase

from src.board_ui import (print_board, print_possible_moves,
                          print_tablebase_info, show_mate_info)
from src.engine_handler import EVAL_DEPTH, get_move_evals
from src.input_handler import handle_user_input


def sort_moves_by_evaluation(
    moves_eval: dict[Move, tuple[int | None, int | None]], is_white_turn: bool
) -> list[tuple[Move, tuple[int | None, int | None]]]:
    """Sorts the evaluated moves based on the score. Higher scores are
    better for White, lower scores are better for Black. Returns a list
    of tuples (Move, (score, mate_value)).
    """

    def sort_key(
        item: tuple[Move, tuple[int | None, int | None]],
    ) -> int:  # TODO: convert this to a one liner
        """Key function for sorting moves."""
        move, (score, _) = item

        return score if score is not None else 0

    moves_list = list(moves_eval.items())

    return sorted(moves_list, key=sort_key, reverse=is_white_turn)


def evaluate_and_show_moves(
    board: Board, engine: SimpleEngine, tablebase: Tablebase | None = None
) -> tuple[dict[Move, tuple[int | None, int | None]], float]:
    """Evaluate moves and display them with timing information. Returns
    a tuple containing the moves evaluation dictionary and the time
    taken for the evaluation.
    """
    start_time = time()

    # Print tablebase info for current position
    if tablebase:
        print_tablebase_info(board, tablebase)

    moves_eval = get_move_evals(
        board, engine, depth=EVAL_DEPTH, tablebase=tablebase
    )

    eval_time = time() - start_time
    sorted_moves = sort_moves_by_evaluation(moves_eval, board.turn)
    print_possible_moves(sorted_moves)

    if sorted_moves:
        show_mate_info(sorted_moves[0], board.turn)

    print(f"\nEvaluation time: {eval_time:.2f} sec\n")

    return moves_eval, eval_time


def play_game(
    board: Board,
    engine: SimpleEngine,
    move_history: list[Move],
    tablebase: Tablebase | None = None,
) -> None:
    """Run the interactive chess game loop."""
    while not board.is_game_over():
        print_board(board)
        evaluate_and_show_moves(board, engine, tablebase)
        move = handle_user_input(board)

        if not move:
            continue

        board.push(move)
        move_history.append(move)
