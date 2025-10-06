from __future__ import annotations

from time import time

from chess import Board, Move, syzygy

CLEAR_BEFORE_PRINT = False  # This should be in config


def clear_terminal() -> None:
    """Clears the terminal screen. Works on Unix-like systems and
    Windows.
    """
    print("\033c", end="")


def print_board(board: Board) -> None:
    """Prints the chess board in a user-friendly format. Clears the
    terminal before printing.
    """
    clear_terminal() if CLEAR_BEFORE_PRINT else None
    print(str(board.unicode(borders=True)).replace("⭘", " ") + "\n")


def display_progress(
    iteration: int, total: int, start_time: float, bar_length: int
) -> None:
    """Displays a progress bar with time estimate. Call this inside a
    loop to update the progress.
    """
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
    """Prints the possible moves along with their evaluation scores.
    Expects a list of tuples (Move, (score, mate_value)).
    """
    print("Possible moves:")

    for move, (score, mate_val) in sorted_moves:
        mate_text = (
            f", Mate in {abs(mate_val)}" if mate_val is not None else ""
        )

        print(f"{move.uci():5s}-> Eval score: {score}{mate_text}")


def show_mate_info(
    best_move_data: tuple[Move, tuple[int | None, int | None]],
    is_white_turn: bool,
) -> None:
    """Display mate information if a mate is found. Expects a tuple (Move, (score, mate_value))."""
    print(
        (
            f"\nMate in {abs(best_move_data[1][1])}"
            if best_move_data[1][1] is not None
            and (best_move_data[1][1] > 0) == is_white_turn
            else ""
        ),
        end="",
    )


def print_tablebase_info(
    board: Board, tablebase: syzygy.Tablebase | None
) -> None:
    """Print information from Syzygy tablebase if available. Shows WDL
    and DTZ if applicable.
    """
    if not tablebase:
        return

    try:
        wdl = tablebase.get_wdl(board)

        if wdl is not None:
            result = "Draw" if wdl == 0 else "Win" if wdl > 0 else "Loss"
            dtz = tablebase.get_dtz(board)
            dtz_str = str(abs(dtz)) if dtz is not None else "N/A"
            print(f"Tablebase: {result} (DTZ: {dtz_str})")

    except IOError:
        pass  # Tablebase file access error

    except ValueError:
        pass  # Invalid position for tablebase

    except IndexError:
        pass  # Index out of bounds in tablebase access


def print_game_over_info(board: Board, move_history: list[Move]) -> None:
    """Prints game over information. Displays the final board, move,
    and result.
    """
    print_board(board)
    print("Game Over!")
    print_move_history(move_history)
    print_game_result(board)


def print_move_history(
    move_history: list[Move], moves_per_line: int = 5
) -> None:
    """Print the game's move history. Formats moves in lines with a set
    number of moves per line.
    """
    print(
        "Moves played:\n"
        + "\n".join(
            "".join(
                f"{i:2d}. {move.uci()}{'  ' if (i % moves_per_line) != 0 else ''}"
                for i, move in enumerate(
                    move_history[j : j + moves_per_line], start=j + 1
                )
            )
            for j in range(0, len(move_history), moves_per_line)
        )
        + "\n"
    )


def print_game_result(board: Board) -> None:
    """Print the game result based on the board state. Handles
    checkmate, stalemate, insufficient material, fifty-move rule, and
    threefold repetition.
    """
    print(
        "Checkmate! Winner: Black"
        if board.is_checkmate() and board.turn
        else (
            "Checkmate! Winner: White"
            if board.is_checkmate()
            else (
                "Stalemate! The game is a draw."
                if board.is_stalemate()
                else (
                    "Insufficient material! The game is a draw."
                    if board.is_insufficient_material()
                    else (
                        "Fifty-move rule! The game is a draw."
                        if board.is_fifty_moves()
                        else (
                            "Threefold repetition! The game is a draw."
                            if board.is_repetition()
                            else f"Game result: {board.result()}"
                        )
                    )
                )
            )
        )
    )
