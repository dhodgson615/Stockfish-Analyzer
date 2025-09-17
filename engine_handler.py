from os import path
from shutil import get_terminal_size
from time import time

from chess import Board, Move
from chess.engine import Limit, SimpleEngine
from chess.syzygy import Tablebase, open_tablebase

from board_ui import display_progress

EVAL_DEPTH = 18
ENGINE_PATH = "/opt/homebrew/bin/stockfish"
SYZYGY_PATH = path.expanduser("~/chess/syzygy")


def get_syzygy_tablebase(filepath=SYZYGY_PATH) -> Tablebase | None:
    """Initialize a Syzygy tablebase."""
    if not path.exists(filepath):
        print(f"Syzygy tablebases not found at {filepath}")
        return None

    try:
        return open_tablebase(filepath)
    except Exception as e:
        print(f"Error loading Syzygy tablebases: {e}")
        return None


def popen_uci(engine_path) -> SimpleEngine:
    """Attempt to open the UCI engine, handling potential errors."""
    try:
        return SimpleEngine.popen_uci(engine_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Engine not found at {engine_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to start engine: {e}")


def get_engine(
    engine_path=ENGINE_PATH, threads=4, hash_size=16384, skill_level=20
) -> SimpleEngine:
    """Initializes and configures the chess engine."""
    return popen_uci(engine_path).configure(
        {"Threads": threads, "Hash": hash_size, "Skill Level": skill_level}
    ) or popen_uci(engine_path)


def evaluate_move(
    board: Board,
    engine: SimpleEngine,
    move: Move,
    depth=EVAL_DEPTH,
    tablebase=None,
) -> tuple[Move, tuple[int | None, int | None]]:
    """Evaluates a single move on the board using tablebase or chess engine."""
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
    board: Board, tablebase
) -> tuple[int | None, int | None] | None:
    """Attempts to evaluate position using Syzygy tablebases.
    Returns (score, mate_value) tuple if successful, None otherwise."""
    if not tablebase:
        return None

    try:
        wdl = tablebase.get_wdl(board)
        if wdl is None:
            return None

        # Convert WDL score to centipawns or mate score
        if wdl == 0:
            return 0, None  # Draw

        # Win for the side to move (positive value)
        if wdl > 0:
            mate_val = tablebase.get_dtz(board)
            score = 1000000 - mate_val  # High score for winning
        # Loss for the side to move (negative value)
        else:
            mate_val = -tablebase.get_dtz(board)
            score = -1000000 - mate_val  # Low score for losing

        # Filter out unreasonably large mate values
        if abs(mate_val or 0) >= 1000:
            mate_val = None

                return move, (
                    score,
                    mate_val if abs(mate_val or 0) < 1000 else None,
                )

        except (IOError, ValueError, IndexError):
            pass  # Tablebase lookup failed

    # Fall back to engine evaluation
    info = engine.analyse(board, Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()
    board.pop()

    return move, (score, mate_val)


def get_move_evals(
    board: Board, engine: SimpleEngine, depth=EVAL_DEPTH, tablebase=None
) -> dict:
    """Evaluates all legal moves on the board."""
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
