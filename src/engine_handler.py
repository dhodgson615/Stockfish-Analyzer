from __future__ import annotations

from os import X_OK, access, name, path, uname
from shutil import get_terminal_size
from subprocess import run
from time import time

import chess
from chess import Board
from chess.engine import Limit, SimpleEngine
from chess.syzygy import Tablebase, open_tablebase

try:
    import board_ui

    print("Imported board_ui from the try block")

except ImportError:
    try:
        import src.board_ui as board_ui

        print("Imported board_ui from the except block")

    except ImportError:
        import board_ui

        print("Imported board_ui from the last except block")


EVAL_DEPTH = 18  # Default depth, used as fallback

ENGINE_PATH = (
    "/opt/homebrew/bin/stockfish"
    if (name == "posix" and uname().machine == "arm64")
    else "/usr/games/stockfish"
)

SYZYGY_PATH = path.expanduser("~/chess/syzygy")


def find_stockfish_path() -> tuple[bool, str]:
    """Find the Stockfish binary path and return existence status and
    path.
    """

    # Check multiple possible locations
    paths_to_check = [
        "/opt/homebrew/bin/stockfish",  # Apple Silicon Mac default
        "/usr/local/bin/stockfish",  # Intel Mac default
        "/opt/local/bin/stockfish",  # MacPorts location
        "/usr/bin/stockfish",  # Uncommon but possible
        "/usr/games/stockfish",  # Linux default
    ]

    # Try using 'which' first (most reliable)
    try:
        result = run(
            ["which", "stockfish"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            filepath = result.stdout.strip()

            if path.exists(filepath) and access(filepath, X_OK):
                return True, filepath

    except Exception:  # FIXME: too broad exception
        pass

    # Check each path in our list
    for filepath in paths_to_check:
        if path.exists(filepath) and access(filepath, X_OK):
            return True, filepath

    # Default fallback path based on OS
    default_path = (
        "/opt/homebrew/bin/stockfish"
        if name == "darwin"
        else "/usr/games/stockfish"
    )

    return False, default_path


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


def get_syzygy_tablebase(filepath: str = SYZYGY_PATH) -> Tablebase | None:
    """Initialize a Syzygy tablebase. Returns None if not found or on
    error.
    """
    if not path.exists(filepath):
        print(f"Syzygy tablebases not found at {filepath}")
        return None

    try:
        return open_tablebase(filepath)

    except Exception as e:  # TODO: handle specific exceptions
        print(f"Error loading Syzygy tablebases: {e}")
        return None


def get_dynamic_eval_depth(board: Board) -> int:
    """Determine the appropriate evaluation depth based on game
    stage.
    """
    return (
        25
        if len(board.piece_map()) - 2 <= 6
        else (
            22
            if len(board.piece_map()) - 2 <= 10
            else (
                14
                if board.fullmove_number <= 10
                and len(board.piece_map()) - 2 >= 20
                else (
                    16
                    if board.fullmove_number <= 15
                    and len(board.piece_map()) - 2 >= 16
                    else 20
                )
            )
        )
    )


def get_move_evals(
    board: Board,
    engine: SimpleEngine,
    depth: int = EVAL_DEPTH,
    tablebase: Tablebase | None = None,
) -> dict[chess.Move, tuple[int | None, int | None]]:
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

        board_ui.display_progress(
            i,
            len(list(board.legal_moves)),
            start_time,
            max(10, get_terminal_size().columns - 40),
        )

    # Clear progress bar
    print(
        "\r" + " " * get_terminal_size().columns + "\r",
        end="",
        flush=True,
    )

    return moves_evaluations


def evaluate_move(
    board: Board,
    engine: SimpleEngine,
    move: chess.Move,
    depth: int = EVAL_DEPTH,
    tablebase: Tablebase | None = None,
) -> tuple[chess.Move, tuple[int | None, int | None]]:
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
        # Ensure we restore the board state
        board.pop()


def try_tablebase_evaluation(
    board: Board, tablebase: Tablebase | None
) -> (
    tuple[int | None, int | None] | None
):  # TODO: Refactor this to use lru_cache
    """Attempts to evaluate the position using the Syzygy tablebase.
    Returns (score, mate_value) tuple if successful, otherwise None.
    """
    if not tablebase:
        return None

    try:
        wdl = tablebase.get_wdl(board)

    except (IOError, ValueError, IndexError):
        return None  # Any tablebase access error

    if wdl is None:
        return None

    if wdl == 0:  # Draw
        return 0, None

    # Get DTZ from tablebase
    try:
        dtz_val = tablebase.get_dtz(board)

    except (IOError, ValueError, IndexError):
        return None  # Any tablebase access error

    # Win/loss for the side to move
    mate_val = (
        dtz_val if wdl > 0 else -dtz_val if dtz_val is not None else None
    )

    score = (
        (1000000 - (mate_val or 0))
        if wdl > 0
        else (-1000000 - (mate_val or 0))
    )

    # Filter out unreasonable mate values
    if abs(mate_val or 0) >= 1000:
        mate_val = None

    return score, mate_val


def get_engine_evaluation(
    board: Board, engine: SimpleEngine, depth: int
) -> tuple[int | None, int | None]:
    """Evaluates a position using the chess engine. Returns (score,
    mate_value) tuple.
    """
    info = engine.analyse(board, Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()

    return score, mate_val
