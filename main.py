"""Script that allows a user to play chess against themselves with move
evaluations provided by a chess engine. The script displays the chess
board, evaluates possible moves, and handles user input for moves. It
also shows game over information including the move history and
result."""

"""TODO:
    - Refactor sorting logic to be more elegant
    - Make exception handling more specific
    - Add unit tests for core functionalities
    - Add Sygygy support for more efficient endgame evaluations
    - Improve user interface for better experience
    - Optimize performance for faster move evaluations
    - Add GUI support for a more interactive experience
    - Add configurable engine settings
    - Add logging for better debugging and tracking
    - Add images to README for better documentation
    - Add graphs to visualize move evaluations over time
"""

import shutil
import time

import chess
import chess.engine

EVAL_DEPTH = 12


def print_board(board: chess.Board):
    """Prints the chess board in a user-friendly format."""
    print(str(board.unicode(borders=True)).replace("⭘", " ") + "\n")


def evaluate_single_move(
    board: chess.Board, engine, move: chess.Move, depth: int = EVAL_DEPTH
):
    """Evaluates a single move on the board using the chess engine."""
    board.push(move)
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()
    board.pop()

    return move, (score, mate_val)


def calculate_and_print_progress(
    iteration: int, total_iterations: int, start_time: float, bar_length: int
):
    """Calculates and prints the progress bar and time estimate."""
    elapsed = time.time() - start_time
    progress_percent = (iteration / total_iterations) * 100

    if iteration == 0:
        avg_time_per_move = 0
    else:
        avg_time_per_move = elapsed / iteration

    remaining_time = avg_time_per_move * (total_iterations - iteration)

    mins, secs = divmod(int(remaining_time), 60)
    time_estimate = f"{mins:02d}:{secs:02d}"

    filled_length = int(round((iteration / total_iterations) * bar_length))
    filled_length = max(0, min(filled_length, bar_length))
    bar = "#" * filled_length + "-" * (bar_length - filled_length)

    print(
        f"\rEvaluating: [{bar}] {progress_percent:.2f}% | "
        f"Remaining: {time_estimate}",
        end="",
        flush=True,
    )


def evaluate_moves(board: chess.Board, engine, depth=EVAL_DEPTH):
    """Evaluates all legal moves on the board using the chess engine and
    displays progress.
    """
    moves_evaluations = {}

    legal_moves = list(board.legal_moves)
    total_moves = len(legal_moves)
    start_time = time.time()
    term_width = shutil.get_terminal_size().columns
    bar_length = max(10, term_width - 40)

    for i, move in enumerate(legal_moves, 1):
        move_evaluation = evaluate_single_move(board, engine, move, depth)
        moves_evaluations[move_evaluation[0]] = move_evaluation[1]
        calculate_and_print_progress(i, total_moves, start_time, bar_length)

    print("\r" + " " * 80 + "\r", end="", flush=True)

    return moves_evaluations


def get_engine(engine_path: str):
    """Initializes and configures the chess engine."""
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    engine.configure(
        {
            "Threads": 2,
            "Hash": 16384,
            "Skill Level": 20,
        }
    )
    
    return engine


def sort_moves_by_evaluation(moves_eval: dict, is_white_turn: bool):
    """Sorts the evaluated moves based on the score, prioritizing for
    the current player.
    """
    if is_white_turn:
        return sorted(
            moves_eval.items(), key=lambda item: item[1][0], reverse=True
        )  # TODO: Make this more elegant
    else:
        return sorted(
            moves_eval.items(), key=lambda item: item[1][0], reverse=False
        )  # TODO: Make this more elegant


def print_possible_moves(sorted_moves: list):
    """Prints the possible moves along with their evaluation scores."""
    print("Possible moves:")
    for move, (score, mate_val) in sorted_moves:
        mate_str = f", Mate in {abs(mate_val)}" if mate_val is not None else ""
        print(f"{move.uci():5s}-> Eval score: {score}{mate_str}")


def handle_user_input(board: chess.Board):
    """Handles user input for the next move."""
    color = "White" if board.turn else "Black"
    user_input = input(
        f"Enter the next move for {color} (SAN or UCI): "
    ).strip()

    try:
        move = board.parse_san(user_input)
    except ValueError:
        try:
            move = chess.Move.from_uci(user_input)
        except Exception:  # TODO: Make this more specific
            print("Invalid move format. Please try again.\n")
            return None

    if move not in board.legal_moves:
        print("Illegal move. Please try again.\n")
        return None

    return move


def print_game_over_info(board: chess.Board, move_history: list):
    """Prints game over information, including the board, move history,
    and result.
    """
    print_board(board)
    print("Game Over!")
    print("Moves played:")

    for idx, move in enumerate(move_history, start=1):
        print(f"{idx:2d}. {move.uci()}", end="  ")
        if idx % 5 == 0:
            print()

    print()

    result = board.result()

    if board.is_checkmate():
        winner = "White" if board.turn == False else "Black"
        print(f"Checkmate! Winner: {winner}")
    elif board.is_stalemate():
        print("Stalemate! The game is a draw.")
    else:
        print(f"Game result: {result}")


def main():
    """Main function to run the interactive chess game."""
    board = chess.Board()
    move_history = []

    engine_path = "/opt/homebrew/bin/stockfish"
    engine = get_engine(engine_path)

    try:
        while not board.is_game_over():
            print_board(board)

            eval_start = time.time()
            moves_eval = evaluate_moves(board, engine, depth=EVAL_DEPTH)
            eval_end = time.time()
            total_eval_time = eval_end - eval_start

            sorted_moves = sort_moves_by_evaluation(moves_eval, board.turn)
            print_possible_moves(sorted_moves)

            if sorted_moves:
                best_move, (best_score, best_mate) = sorted_moves[0]
                if best_mate is not None and (
                    (board.turn and best_mate > 0)
                    or (not board.turn and best_mate < 0)
                ):
                    print(f"\nMate in {abs(best_mate)}")

            print(f"\nEvaluation time: {total_eval_time:.2f} sec\n")

            move = handle_user_input(board)

            if move:
                board.push(move)
                move_history.append(move)
            else:
                continue

        print_game_over_info(board, move_history)

    finally:
        engine.quit()


if __name__ == "__main__":
    main()
