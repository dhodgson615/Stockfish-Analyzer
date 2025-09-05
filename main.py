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


def print_board(board: chess.Board) -> None:
    """Prints the chess board in a user-friendly format."""
    print(str(board.unicode(borders=True)).replace("⭘", " ") + "\n")


def evaluate_single_move(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    move: chess.Move,
    depth=EVAL_DEPTH,
) -> tuple[chess.Move, tuple[int | None, int | None]]:
    """Evaluates a single move on the board using the chess engine."""
    board.push(move)
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()
    board.pop()

    return move, (score, mate_val)


def display_progress(
    iteration: int,
    total: int,
    start_time: float,
    bar_length: int
) -> None:
    """Displays a progress bar with time estimate."""
    elapsed = time.time() - start_time
    progress_ratio = iteration / total

    # Calculate time estimate
    avg_time = elapsed / max(1, iteration)  # Avoid division by zero
    remaining_secs = avg_time * (total - iteration)
    mins, secs = divmod(int(remaining_secs), 60)

    # Create progress bar
    filled = int(round(progress_ratio * bar_length))
    filled = max(0, min(filled, bar_length))
    bar = "#" * filled + "-" * (bar_length - filled)

    print(
        f"\rEvaluating: [{bar}] {progress_ratio*100:.1f}% | "
        f"Remaining: {mins:02d}:{secs:02d}",
        end="",
        flush=True,
    )


def evaluate_moves(board: chess.Board, engine, depth=EVAL_DEPTH) -> dict:
    """Evaluates all legal moves on the board."""
    moves_evaluations = {}
    legal_moves = list(board.legal_moves)
    total_moves = len(legal_moves)
    start_time = time.time()
    term_width = shutil.get_terminal_size().columns
    bar_length = max(10, term_width - 40)

    for i, move in enumerate(legal_moves, 1):
        move_obj, score_data = evaluate_single_move(board, engine, move, depth)
        moves_evaluations[move_obj] = score_data
        display_progress(i, total_moves, start_time, bar_length)

    # Clear progress bar
    clear_line = "\r" + " " * term_width + "\r"
    print(clear_line, end="", flush=True)

    return moves_evaluations


def get_engine(
    engine_path: str, threads=2, hash_size=16384, skill_level=20
) -> chess.engine.SimpleEngine:
    """Initializes and configures the chess engine."""
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    engine.configure(
        {
            "Threads": threads,
            "Hash": hash_size,
            "Skill Level": skill_level,
        }
    )

    return engine


def sort_moves_by_evaluation(moves_eval: dict, is_white_turn: bool) -> list:
    """Sorts the evaluated moves based on the score."""
    return sorted(
        moves_eval.items(), key=lambda item: item[1][0], reverse=is_white_turn
    )


def print_possible_moves(sorted_moves: list) -> None:
    """Prints the possible moves along with their evaluation scores."""
    print("Possible moves:")
    for move, (score, mate_val) in sorted_moves:
        mate_info = (
            f", Mate in {abs(mate_val)}" if mate_val is not None else ""
        )
        print(f"{move.uci():5s}-> Eval score: {score}{mate_info}")


def parse_move_input(board, user_input) -> chess.Move | None:
    """Parse user input as a chess move."""
    try:
        return board.parse_san(user_input)
    except ValueError:
        try:
            return chess.Move.from_uci(user_input)
        except (ValueError, IndexError):
            print("Invalid move format. Please try again.\n")
            return None


def handle_user_input(board: chess.Board) -> chess.Move | None:
    """Handles user input for the next move."""
    color = "White" if board.turn else "Black"
    user_input = input(
        f"Enter the next move for {color} (SAN or UCI): "
    ).strip()

    move = parse_move_input(board, user_input)

    if move and move in board.legal_moves:
        return move
    elif move:
        print("Illegal move. Please try again.\n")

    return None


def print_move_history(move_history, moves_per_line=5) -> None:
    """Print the game's move history."""
    print("Moves played:")
    for idx, move in enumerate(move_history, start=1):
        print(f"{idx:2d}. {move.uci()}", end="  ")
        if idx % moves_per_line == 0:
            print()
    print()


def print_game_result(board) -> None:
    """Print the game result based on the board state."""
    if board.is_checkmate():
        winner = "Black" if board.turn else "White"
        print(f"Checkmate! Winner: {winner}")
    elif board.is_stalemate():
        print("Stalemate! The game is a draw.")
    else:
        print(f"Game result: {board.result()}")


def print_game_over_info(board: chess.Board, move_history: list) -> None:
    """Prints game over information."""
    print_board(board)
    print("Game Over!")
    print_move_history(move_history)
    print_game_result(board)


def show_mate_info(best_move_data, is_white_turn):
    """Display mate information if a mate is found."""
    _, (_, mate_val) = best_move_data
    if mate_val is not None:
        is_winning_mate = (is_white_turn and mate_val > 0) or (
            not is_white_turn and mate_val < 0
        )
        if is_winning_mate:
            print(f"\nMate in {abs(mate_val)}")


def evaluate_and_show_moves(board, engine):
    """Evaluate moves and display them with timing information."""
    start_time = time.time()
    moves_eval = evaluate_moves(board, engine, depth=EVAL_DEPTH)
    eval_time = time.time() - start_time

    sorted_moves = sort_moves_by_evaluation(moves_eval, board.turn)
    print_possible_moves(sorted_moves)

    if sorted_moves:
        show_mate_info(sorted_moves[0], board.turn)

    print(f"\nEvaluation time: {eval_time:.2f} sec\n")
    return moves_eval, eval_time


def play_game(board, engine, move_history):
    """Run the interactive chess game loop."""
    while not board.is_game_over():
        print_board(board)

        evaluate_and_show_moves(board, engine)

        move = handle_user_input(board)
        if not move:
            continue

        board.push(move)
        move_history.append(move)


def main():
    """Main function to run the interactive chess game."""
    board = chess.Board()
    move_history = []

    engine_path = "/opt/homebrew/bin/stockfish"
    engine = get_engine(engine_path)

    try:
        play_game(board, engine, move_history)
        print_game_over_info(board, move_history)
    finally:
        engine.quit()


if __name__ == "__main__":
    main()
