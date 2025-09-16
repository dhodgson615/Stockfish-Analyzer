import shutil
import time
import os

from chess import Board, Move
from chess.engine import Limit, SimpleEngine
from chess.syzygy import open_tablebase

from board_ui import display_progress

EVAL_DEPTH = 12
ENGINE_PATH = "/opt/homebrew/bin/stockfish"
SYZYGY_PATH = os.path.expanduser("~/chess/syzygy")  # Default path to Syzygy tablebases


def get_syzygy_tablebase(path=SYZYGY_PATH):
    """Initialize a Syzygy tablebase."""
    if not os.path.exists(path):
        print(f"Syzygy tablebases not found at {path}")
        return None

    try:
        return chess.syzygy.open_tablebase(path)
    except Exception as e:
        print(f"Error loading Syzygy tablebases: {e}")
        return None


def get_engine(
    engine_path=ENGINE_PATH, threads=4, hash_size=16384, skill_level=20
) -> SimpleEngine:
    """Initializes and configures the chess engine."""
    engine = SimpleEngine.popen_uci(engine_path)
    engine.configure(
        {
            "Threads": threads,
            "Hash": hash_size,
            "Skill Level": skill_level,
        }
    )

    return engine


def evaluate_move(
    board: Board,
    engine: SimpleEngine,
    move: Move,
    depth=EVAL_DEPTH,
    tablebase=None,
) -> tuple[Move, tuple[int | None, int | None]]:
    """Evaluates a single move on the board using tablebase or chess engine."""
    board.push(move)

    # Try tablebase first if available and position has few enough pieces
    if tablebase and sum(1 for _ in board.piece_map()) <= tablebase.max_pieces:
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
        except Exception:
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
    legal_moves = list(board.legal_moves)
    total_moves = len(legal_moves)
    start_time = time()
    term_width = get_terminal_size().columns
    bar_length = max(10, term_width - 40)

    for i, move in enumerate(legal_moves, 1):
        move_obj, score_data = evaluate_move(
            board, engine, move, depth, tablebase
        )
        moves_evaluations[move_obj] = score_data
        display_progress(i, total_moves, start_time, bar_length)

    # Clear progress bar
    clear_line = "\r" + " " * term_width + "\r"
    print(clear_line, end="", flush=True)

    return moves_evaluations
