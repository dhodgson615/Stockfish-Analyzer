from os import path
from shutil import get_terminal_size
from time import time

from chess import Board, Move
from chess.engine import Limit, SimpleEngine
from chess.syzygy import open_tablebase, Tablebase

from board_ui import display_progress

EVAL_DEPTH = 12
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


def popen_uci(engine_path):
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
) -> tuple[
    Move, tuple[int | None, int | None]
]:  # TODO: Make this function use less nesting
    """Evaluates a single move on the board using tablebase or chess
    engine.
    """
    board.push(move)

    # Try tablebase first if available
    if tablebase:
        try:
            wdl = tablebase.get_wdl(board)
            if wdl is not None:
                # Convert WDL score (-2 to +2) to centipawns or mate score
                if wdl == 0:
                    score, mate_val = 0, None  # Draw
                elif wdl > 0:
                    # Win for the side to move (positive value)
                    mate_val = tablebase.get_dtz(board)
                    score = 1000000 - mate_val  # High score for winning
                else:
                    # Loss for the side to move (negative value)
                    mate_val = -tablebase.get_dtz(board)
                    score = -1000000 - mate_val  # Low score for losing

                board.pop()

                return move, (
                    score,
                    mate_val if abs(mate_val or 0) < 1000 else None,
                )
        except Exception:  # TODO: Specify exception type
            pass  # Fall back to engine if tablebase lookup fails

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
