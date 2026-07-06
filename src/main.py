from contextlib import suppress
from dataclasses import dataclass, field
from os import X_OK, access, name, path, uname
from platform import system
from shutil import get_terminal_size, which
from sys import exit
from time import time
from typing import Optional

from chess import Board, Move
from chess.engine import Limit, SimpleEngine
from chess.syzygy import Tablebase, open_tablebase

# TODO: refactor the script to use as little try/except as possible
# TODO: refactor this script so that it uses more idiomatic Python


def main() -> None:
    """Main function to run the interactive chess game."""
    app_config = get_default_config()
    print(f"Engine: {app_config.engine_path}")
    print(f"Threads: {app_config.threads}")
    print(f"Hash: {app_config.hash_size}MB")
    print(f"Skill: {app_config.skill_level}")
    print(f"Depth: {app_config.eval_depth}")

    board = Board()
    move_history: list[Move] = []

    engine = get_engine(
        engine_path=app_config.engine_path,
        threads=app_config.threads,
        hash_size=app_config.hash_size,
        skill_level=app_config.skill_level,
    )

    tablebase = get_syzygy_tablebase(app_config.syzygy_path)
    print("Tablebases loaded" if tablebase else "Tablebases not available")

    try:
        play_game(board, engine, move_history, tablebase)
        print_game_over_info(board, move_history)

        if tablebase:
            print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


def parse_move_input(board: Board, user_input: str) -> Optional[Move]:
    """Parse user input as a chess move. Tries SAN first, then UCI.
    Returns a Move object if successful, otherwise None.
    """
    # Try SAN first
    with suppress(ValueError):
        return board.parse_san(user_input)

    # Try UCI next
    with suppress(ValueError):
        return Move.from_uci(user_input)

    return None


def handle_user_input(board: Board) -> Optional[Move]:
    """Handles user input for making moves. Returns a valid Move object
    or None if the input is invalid.
    """
    user_input = input("Enter your move (UCI or SAN): ")
    return process_user_input(board, user_input)


def process_user_input(board: Board, user_input: str) -> Optional[Move]:
    """Processes a user input string and returns a valid Move object
    or None if the input is invalid. Separated from handle_user_input
    for better testability.
    """
    if user_input.lower() in ["quit", "q", "exit"]:
        print("Exiting game...")
        exit(0)

    move = parse_move_input(board, user_input)

    if move is None:
        print("Invalid move format. Please try again.\n")
        return None

    if move not in board.legal_moves:
        print("Illegal move. Please try again.\n")
        return None

    return move


def get_default_engine_path() -> str:
    """Determine the default Stockfish engine path based on OS."""
    return (
        "/opt/homebrew/bin/stockfish"
        if system() == "Darwin" and uname().machine == "arm64"
        else (
            "/usr/local/bin/stockfish"
            if system() == "Darwin"
            else "/usr/games/stockfish"
        )
    )


@dataclass
class EngineConfig:
    """Configuration for the chess engine."""

    engine_path: str = field(default_factory=get_default_engine_path)
    threads: int = 4
    hash_size: int = 16384
    skill_level: int = 20
    eval_depth: int = 18

    syzygy_path: str = field(
        default_factory=lambda: path.expanduser("~/chess/syzygy")
    )

    def __post_init__(self) -> None:
        """Expand user paths after initialization."""
        self.syzygy_path = path.expanduser(self.syzygy_path)


def get_default_config() -> EngineConfig:
    """Get default configuration without parsing any arguments."""
    return EngineConfig()


CLEAR_BEFORE_PRINT = False  # This should be in config


def clear_terminal() -> None:
    """Clears the terminal screen. Works on Unix-like systems and
    Windows.
    """
    print("\033c", end="")


def print_board(board: Board) -> None:
    """Prints the chess board in a user-friendly format. Clears the
    terminal before printing if configured.
    """
    if CLEAR_BEFORE_PRINT:
        clear_terminal()

    formatted_board = board.unicode(borders=True).replace("⭘", " ")
    print(f"{formatted_board}\n")


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
    sorted_moves: list[tuple[Move, tuple[Optional[int], Optional[int]]]],
) -> None:
    """Prints the possible moves along with their evaluation scores.
    Expects a list of tuples (Move, (score, mate_value)).
    """
    print(
        "Possible moves:\n"
        + "\n".join(
            f"{move.uci():5s}-> Eval score: {score}"
            + (f", Mate in {abs(mate_val)}" if mate_val else "")
            for move, (score, mate_val) in sorted_moves
        )
    )


def show_mate_info(
    best_move_data: tuple[Move, tuple[Optional[int], Optional[int]]],
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


def print_tablebase_info(board: Board, tablebase: Optional[Tablebase]) -> None:
    """Print information from Syzygy tablebase if available. Shows WDL
    and DTZ if applicable, using a single `with` statement for suppression.
    """
    if tablebase:
        with suppress(IOError, ValueError, IndexError):
            wdl = tablebase.get_wdl(board)

            if wdl is None:
                return

            try:
                dtz = tablebase.get_dtz(board)

            except (IOError, ValueError, IndexError):
                dtz = None

            print(
                f"Tablebase: "
                f"{'Draw' if wdl == 0 else 'Win' if wdl > 0 else 'Loss'} "
                f"(DTZ: {str(abs(dtz)) if dtz is not None else 'N/A'})"
            )


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


EVAL_DEPTH = 18

ENGINE_PATH = (
    "/opt/homebrew/bin/stockfish"
    if (name == "posix" and uname().machine == "arm64")
    else "/usr/games/stockfish"
)

SYZYGY_PATH = path.expanduser("~/chess/syzygy")


def find_stockfish_path() -> tuple[bool, str]:
    """Find Stockfish executable: check PATH via shutil.which then common locations.
    Returns (found: bool, path: str)."""
    candidate = which("stockfish")

    if candidate and path.exists(candidate) and access(candidate, X_OK):
        return True, candidate

    for p in (
        "/opt/homebrew/bin/stockfish",  # macOS Homebrew (Apple Silicon)
        "/usr/local/bin/stockfish",  # macOS Brew (Intel) / custom
        "/opt/local/bin/stockfish",  # MacPorts
        "/usr/bin/stockfish",
        "/usr/games/stockfish",  # Debian/Ubuntu
    ):
        if path.exists(p) and access(p, X_OK):
            return True, p

    default = (
        "/opt/homebrew/bin/stockfish"
        if system() == "Darwin"
        else "/usr/games/stockfish"
    )

    return False, default


def get_engine(
    engine_path: str = ENGINE_PATH,
    threads: int = 4,
    hash_size: int = 16384,
    skill_level: int = 20,
) -> SimpleEngine:
    """Initializes and configures the chess engine. Returns the engine
    instance.
    """
    engine = SimpleEngine.popen_uci(engine_path)

    engine.configure(
        {"Threads": threads, "Hash": hash_size, "Skill Level": skill_level}
    )

    return engine


def get_syzygy_tablebase(filepath: str = SYZYGY_PATH) -> Optional[Tablebase]:
    """Initialize a Syzygy tablebase. Returns None if not found or on
    error.
    """
    if path.exists(filepath):
        try:
            return open_tablebase(filepath)

        except Exception as e:  # TODO: handle specific exceptions
            print(f"Error loading Syzygy tablebases: {e}")
            return None

    print(f"Syzygy tablebases not found at {filepath}")
    return None


def get_dynamic_eval_depth(board: Board) -> int:
    """Determine the appropriate evaluation depth based on game stage."""
    non_king_pieces = len(board.piece_map()) - 2
    moves = board.fullmove_number

    if non_king_pieces <= 6:
        return 25

    if non_king_pieces <= 10:
        return 22

    if moves <= 10 and non_king_pieces >= 20:
        return 14

    if moves <= 15 and non_king_pieces >= 16:
        return 16

    return 20


def get_move_evals(
    board: Board,
    engine: SimpleEngine,
    depth: int = EVAL_DEPTH,
    tablebase: Optional[Tablebase] = None,
) -> dict[Move, tuple[Optional[int], Optional[int]]]:
    """Evaluates all legal moves on the board. Returns a dictionary
    mapping moves to their (score, mate_value) tuples.
    """
    moves_evaluations = {}
    start_time = time()

    for i, move in enumerate(list(board.legal_moves), 1):
        move_obj, score_data = evaluate_move(
            board, engine, move, depth, tablebase
        )

        moves_evaluations[move_obj] = score_data

        display_progress(
            i,
            len(list(board.legal_moves)),
            start_time,
            max(10, get_terminal_size().columns - 40),
        )

    print(
        "\r" + " " * get_terminal_size().columns + "\r",
        end="",
        flush=True,
    )

    return moves_evaluations


def evaluate_move(
    board: Board,
    engine: SimpleEngine,
    move: Move,
    depth: int = EVAL_DEPTH,
    tablebase: Optional[Tablebase] = None,
) -> tuple[Move, tuple[Optional[int], Optional[int]]]:
    """Evaluates a single move on the board using tablebase or chess
    engine. Returns the move and its (score, mate_value) tuple.
    """
    board.push(move)

    try:
        return move, (
            try_tablebase_evaluation(board, tablebase)
            or get_engine_evaluation(board, engine, depth)
        )

    finally:
        board.pop()


def try_tablebase_evaluation(
    board: Board, tablebase: Optional[Tablebase]
) -> Optional[tuple[Optional[int], Optional[int]]]:
    """Attempt tablebase evaluation; return (score, mate_value) or
    None.
    """
    if tablebase is None:
        return None

    try:
        wdl = tablebase.get_wdl(board)

        if wdl is None:
            return None

        if wdl == 0:
            return 0, None

        dtz = tablebase.get_dtz(board)

    except (IOError, ValueError, IndexError):
        return None

    mate_val = (
        None
        if dtz is None
        else (
            None
            if abs(dtz if wdl > 0 else -dtz) >= 1000
            else (dtz if wdl > 0 else -dtz)
        )
    )

    score = (
        (1000000 - (mate_val or 0))
        if wdl > 0
        else (-1000000 - (mate_val or 0))
    )

    return score, mate_val


def get_engine_evaluation(
    board: Board, engine: SimpleEngine, depth: int
) -> tuple[Optional[int], Optional[int]]:
    """Evaluates a position using the chess engine. Returns (score,
    mate_value) tuple.
    """
    info = engine.analyse(board, Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()
    return score, mate_val


def play_game(
    board: Board,
    engine: SimpleEngine,
    move_history: list[Move],
    tablebase: Optional[Tablebase] = None,
) -> None:
    """Run the interactive chess game loop. Continues until the game is
    over. Displays the board, evaluates moves, and handles user input
    for moves.
    """
    while not board.is_game_over():
        print_board(board)
        evaluate_and_show_moves(board, engine, tablebase)
        move = handle_user_input(board)

        if move:
            board.push(move)
            move_history.append(move)


def evaluate_and_show_moves(
    board: Board,
    engine: SimpleEngine,
    tablebase: Optional[Tablebase] = None,
    app_config: Optional[EngineConfig] = None,
) -> tuple[dict[Move, tuple[Optional[int], Optional[int]]], float]:
    """Evaluate moves and display them with timing information. Returns
    a tuple containing the moves evaluation dictionary and the time
    taken for the evaluation.
    """  # FIXME: mixes evaluation logic with display logic (wrong module)
    start_time = time()

    if tablebase:
        print_tablebase_info(board, tablebase)

    eval_depth = (
        app_config.eval_depth if app_config else get_dynamic_eval_depth(board)
    )

    moves_eval = get_move_evals(
        board,
        engine,
        depth=eval_depth,
        tablebase=tablebase,
    )

    eval_time = time() - start_time
    sorted_moves = sort_moves_by_evaluation(moves_eval, board.turn)
    print_possible_moves(sorted_moves)

    if sorted_moves:
        show_mate_info(sorted_moves[0], board.turn)

    print(f"\nEvaluation time: {eval_time:.2f} sec\n")
    return moves_eval, eval_time


def sort_moves_by_evaluation(
    moves_eval: dict[Move, tuple[Optional[int], Optional[int]]],
    is_white_turn: bool,
) -> list[tuple[Move, tuple[Optional[int], Optional[int]]]]:
    """Sorts the evaluated moves based on the score. Higher scores are
    better for White, lower scores are better for Black. Returns a list
    of tuples (Move, (score, mate_value)).
    """
    return sorted(
        moves_eval.items(),
        key=lambda item: item[1][0] if item[1][0] is not None else 0,
        reverse=is_white_turn,
    )


def get_move_score(
    item: tuple[Move, tuple[Optional[int], Optional[int]]],
) -> int:
    """Key function for sorting moves. Takes (Move, (score,
    mate_value)) and returns score for sorting.
    """
    return item[1][0] if item[1][0] is not None else 0


if __name__ == "__main__":
    main()
