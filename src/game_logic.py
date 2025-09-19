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
    """Sorts the evaluated moves based on the score."""
    moves = list(moves_eval.items())
    indexed_scores = []

    for i in range(len(moves)):
        score = moves[i][1][0]

        if score is not None:
            indexed_scores.append((score, i))

        else:
            indexed_scores.append((0, i))  # Default score for None values

    indexed_scores.sort(reverse=is_white_turn)

    return [moves[idx] for _, idx in indexed_scores]


def evaluate_and_show_moves(
    board: Board, engine: SimpleEngine, tablebase: Tablebase | None = None
) -> tuple[dict[Move, tuple[int | None, int | None]], float]:
    """Evaluate moves and display them with timing information."""
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
