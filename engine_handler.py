import shutil
import time

from chess import Board, Move
from chess.engine import Limit, SimpleEngine

from board_ui import display_progress

EVAL_DEPTH = 12
ENGINE_PATH = "/opt/homebrew/bin/stockfish"


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
) -> tuple[Move, tuple[int | None, int | None]]:
    """Evaluates a single move on the board using the chess engine.
    Returns the move and its evaluation score along with mate info.
    """
    board.push(move)
    info = engine.analyse(board, Limit(depth=depth))
    score_obj = info["score"].white()
    score = score_obj.score(mate_score=1000000)
    mate_val = score_obj.mate()
    board.pop()

    return move, (score, mate_val)


def get_move_evals(
    board: Board, engine: SimpleEngine, depth=EVAL_DEPTH
) -> dict:
    """Evaluates all legal moves on the board."""
    moves_evaluations = {}
    legal_moves = list(board.legal_moves)
    total_moves = len(legal_moves)
    start_time = time.time()
    term_width = shutil.get_terminal_size().columns
    bar_length = max(10, term_width - 40)

    for i, move in enumerate(legal_moves, 1):
        move_obj, score_data = evaluate_move(board, engine, move, depth)
        moves_evaluations[move_obj] = score_data
        display_progress(i, total_moves, start_time, bar_length)

    # Clear progress bar
    clear_line = "\r" + " " * term_width + "\r"
    print(clear_line, end="", flush=True)

    return moves_evaluations
