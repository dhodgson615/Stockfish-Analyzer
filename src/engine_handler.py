from __future__ import annotations

import os
import shutil
import time

import chess
import chess.engine
import chess.syzygy

try:
    import board_ui

except ImportError:
    import src.board_ui as board_ui


EVAL_DEPTH = 18  # Default depth, used as fallback
ENGINE_PATH = "/opt/homebrew/bin/stockfish"
SYZYGY_PATH = os.path.expanduser("~/chess/syzygy")


def get_dynamic_eval_depth(board: chess.Board) -> int:
    """Determine the appropriate evaluation depth based on game stage.

    Game stages are determined by:
    - Piece count: More pieces = earlier stage
    - Move count: More moves = later stage

    Returns:
        Opening (early game): 12-15 depth (faster evaluation)
        Middlegame: 18-20 depth (balanced approach)
        Endgame: 20-25 depth (deeper search, fewer pieces)
    """
    # Count pieces on the board (excluding kings)
    piece_count = len(board.piece_map()) - 2  # Subtract 2 kings
    move_count = board.fullmove_number

    # Endgame: Few pieces remaining (typically <= 10 pieces)
    if piece_count <= 10:
        if piece_count <= 6:
            return 25  # Very few pieces, can search deeply
        else:
            return 22  # Transitioning to endgame
    
    # Opening: Many pieces, early moves (first 10 moves)
    elif move_count <= 10 and piece_count >= 20:
        return 14  # Fast evaluation in opening
    
    # Late opening/early middlegame
    elif move_count <= 15 and piece_count >= 16:
        return 16
    
    # Middlegame: Most complex phase
    else:
        return 20  # Slightly deeper than default for tactical precision


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


def get_engine(
    engine_path: str = ENGINE_PATH,
    threads: int = 4,
    hash_size: int = 16384,
    skill_level: int = 20,
) -> chess.engine.SimpleEngine:
    """Initializes and configures the chess engine. Returns the engine
    instance.
    """
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)

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
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()

    return score, mate_val


def get_move_evals(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    depth: int = EVAL_DEPTH,
    tablebase: chess.syzygy.Tablebase | None = None,
) -> dict[chess.Move, tuple[int | None, int | None]]:
    """Evaluates all legal moves on the board. Returns a dictionary
    mapping moves to their (score, mate_value) tuples.
    """
    moves_evaluations = {}
    start_time = time.time()

    for i, move in enumerate(list(board.legal_moves), 1):
        move_obj, score_data = evaluate_move(
            board, engine, move, depth, tablebase
        )

        moves_evaluations[move_obj] = score_data

        board_ui.display_progress(
            i,
            len(list(board.legal_moves)),
            start_time,
            max(10, shutil.get_terminal_size().columns - 40),
        )

    # Clear progress bar
    print(
        "\r" + " " * shutil.get_terminal_size().columns + "\r",
        end="",
        flush=True,
    )

    return moves_evaluations
