from __future__ import annotations

from time import time

from chess import Board, Move
from chess.syzygy import Tablebase


def clear_terminal() -> None:
    """Clears the terminal screen."""
    print("\033c", end="")


def print_board(board: Board) -> None:
    """Prints the chess board in a user-friendly format. Clears the
    terminal before printing.
    """
    clear_terminal()
    print(str(board.unicode(borders=True)).replace("⭘", " ") + "\n")


def display_progress(
    iteration: int, total: int, start_time: float, bar_length: int
) -> None:
    """Displays a progress bar with time estimate."""
    elapsed = time() - start_time
    progress_ratio = iteration / total

    avg_time = elapsed / max(1, iteration)  # Avoid division by zero
    remaining_secs = avg_time * (total - iteration)
    mins, secs = divmod(int(remaining_secs), 60)

    filled = max(0, min(int(round(progress_ratio * bar_length)), bar_length))
    bar = "#" * filled + "-" * (bar_length - filled)

    print(
        f"\rEvaluating: [{bar}] {progress_ratio*100:.1f}% | "
        f"Remaining: {mins:02d}:{secs:02d}",
        end="",
        flush=True,
    )


def print_possible_moves(
    sorted_moves: list[tuple[Move, tuple[int | None, int | None]]],
) -> None:
    """Prints the possible moves along with their evaluation scores."""
    print("Possible moves:")

    for move, (score, mate_val) in sorted_moves:
        mate_text = (
            f", Mate in {abs(mate_val)}" if mate_val is not None else ""
        )
        print(f"{move.uci():5s}-> Eval score: {score}{mate_text}")


def print_move_history(
    move_history: list[Move], moves_per_line: int = 5
) -> None:
    """Print the game's move history."""
    print("Moves played:")

    for idx, move in enumerate(move_history, start=1):
        end_char = "\n" if idx % moves_per_line == 0 else "  "
        print(f"{idx:2d}. {move.uci()}", end=end_char)

    if len(move_history) % moves_per_line != 0:
        print()

    print()


def print_game_result(board: Board) -> None:
    """Print the game result based on the board state."""
    if board.is_checkmate():
        winner = "Black" if board.turn else "White"
        print(f"Checkmate! Winner: {winner}")
    elif board.is_stalemate():
        print("Stalemate! The game is a draw.")
    elif board.is_insufficient_material():
        print("Insufficient material! The game is a draw.")
    elif board.is_fifty_moves():
        print("Fifty-move rule! The game is a draw.")
    elif board.is_repetition():
        print("Threefold repetition! The game is a draw.")
    else:
        print(f"Game result: {board.result()}")


def print_game_over_info(board: Board, move_history: list[Move]) -> None:
    """Prints game over information."""
    print_board(board)
    print("Game Over!")
    print_move_history(move_history)
    print_game_result(board)


def show_mate_info(
    best_move_data: tuple[Move, tuple[int | None, int | None]],
    is_white_turn: bool,
) -> None:
    """Display mate information if a mate is found."""
    _, (_, mate_val) = best_move_data

    if mate_val is not None and (mate_val > 0) == is_white_turn:
        print(f"\nMate in {abs(mate_val)}")


def print_tablebase_info(board: Board, tablebase: Tablebase) -> None:
    """Print information from Syzygy tablebase if available."""
    if not tablebase:
        return

    try:
        wdl = tablebase.get_wdl(board)

        if wdl is not None:
            result = "Draw" if wdl == 0 else "Win" if wdl > 0 else "Loss"
            dtz = tablebase.get_dtz(board)
            dtz_str = str(abs(dtz)) if dtz is not None else "N/A"
            print(f"Tablebase: {result} (DTZ: {dtz_str})")

    except (
        IOError,
        ValueError,
        IndexError,
    ):  # TODO: handle specific exceptions
        pass  # Tablebase lookup failed
