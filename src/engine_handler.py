from __future__ import annotations

import os
import shutil
import time

import chess
import chess.engine
import chess.syzygy

import src.board_ui

EVAL_DEPTH = 18
ENGINE_PATH = "/opt/homebrew/bin/stockfish"
SYZYGY_PATH = os.path.expanduser("~/chess/syzygy")


def get_syzygy_tablebase(
    filepath: str = SYZYGY_PATH,
) -> chess.syzygy.Tablebase | None:
    """Initialize a Syzygy tablebase. Returns None if not found or on
    error.
    """
    if not os.path.exists(filepath):
        print(f"Syzygy tablebases not found at {filepath}")
        return None

    try:
        return chess.syzygy.open_tablebase(filepath)

    except Exception as e:  # TODO: handle specific exceptions
        print(f"Error loading Syzygy tablebases: {e}")
        return None


def popen_uci(engine_path: str) -> chess.engine.SimpleEngine:
    """Attempt to open the UCI engine, handling potential errors.
    Returns the engine instance if successful.
    """
    try:
        return chess.engine.SimpleEngine.popen_uci(engine_path)

    except FileNotFoundError:
        raise FileNotFoundError(f"Engine not found at {engine_path}")

    except Exception as e:
        raise RuntimeError(f"Failed to start engine: {e}")


def get_engine(
    engine_path: str = ENGINE_PATH,
    threads: int = 4,
    hash_size: int = 16384,
    skill_level: int = 20,
) -> chess.engine.SimpleEngine:
    """Initializes and configures the chess engine. Returns the engine
    instance.
    """
    engine = popen_uci(engine_path)
    engine.configure(
        {"Threads": threads, "Hash": hash_size, "Skill Level": skill_level}
    )

    return engine


def evaluate_move(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    move: chess.Move,
    depth: int = EVAL_DEPTH,
    tablebase: chess.syzygy.Tablebase | None = None,
) -> tuple[chess.Move, tuple[int | None, int | None]]:
    """Evaluates a single move on the board using tablebase or chess
    engine. Returns the move and its (score, mate_value) tuple.
    """
    board.push(move)

    try:
        # First attempt tablebase evaluation if available
        tablebase_result = try_tablebase_evaluation(board, tablebase)

        if tablebase_result:
            return move, tablebase_result

        # Fall back to engine evaluation
        return move, get_engine_evaluation(board, engine, depth)

    finally:
        # Ensure we restore the board state
        board.pop()


def try_tablebase_evaluation(
    board: chess.Board, tablebase: chess.syzygy.Tablebase | None
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
    board: chess.Board, engine: chess.engine.SimpleEngine, depth: int
) -> tuple[int | None, int | None]:
    """Evaluates a position using the chess engine. Returns (score,
    mate_value) tuple.
    """
    info = engine.analyse(board, Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()

    return score, mate_val


def get_move_evals(
    board: Board,
    engine: SimpleEngine,
    depth: int = EVAL_DEPTH,
    tablebase: Tablebase | None = None,
) -> dict[Move, tuple[int | None, int | None]]:
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

    # Clear progress bar
    print("\r" + " " * get_terminal_size().columns + "\r", end="", flush=True)

    return moves_evaluations
