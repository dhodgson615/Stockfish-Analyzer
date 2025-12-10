from __future__ import annotations

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from json import JSONDecodeError, dump, load
from os import X_OK, access, name, path, uname
from pathlib import Path
from platform import system
from shutil import get_terminal_size
from subprocess import run
from sys import exit
from time import time
from typing import Any, Optional, cast

import chess.engine
import chess.syzygy
from chess import Board, Move, syzygy
from chess.engine import Limit, SimpleEngine
from chess.syzygy import Tablebase, open_tablebase

# TODO: refactor the script to use as little try/except as possible


def main() -> None:
    """Main function to run the interactive chess game."""
    app_config = parse_config()
    print(f"Engine: {app_config.engine_path}")

    print(
        f"Threads: {app_config.threads}, Hash: {app_config.hash_size}MB, "
        f"Skill: {app_config.skill_level}, Depth: {app_config.eval_depth}"
    )

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
        play_game(board, engine, move_history, tablebase, app_config)
        print_game_over_info(board, move_history)

        if tablebase:
            print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


def parse_move_input(board: Board, user_input: str) -> Move | None:
    """Parse user input as a chess move. Tries SAN first, then UCI.
    Returns a Move object if successful, otherwise None.
    """
    try:
        return board.parse_san(user_input)

    except ValueError:
        try:
            return Move.from_uci(user_input)

        except ValueError:
            return None


def handle_user_input(board: Board) -> Move | None:
    """Handles user input for making moves. Returns a valid Move object
    or None if the input is invalid.
    """
    user_input = input("Enter your move (UCI or SAN): ")

    return process_user_input(board, user_input)


def process_user_input(board: Board, user_input: str) -> Move | None:
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


def create_argument_parser() -> ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = ArgumentParser(
        description="Interactive chess analysis with Stockfish engine",
        formatter_class=RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 src/main.py
  python3 src/main.py --engine-path /usr/local/bin/stockfish
  python3 src/main.py --threads 8 --hash-size 8192 --depth 20
  python3 src/main.py --config my_config.json
  python3 src/main.py --skill-level 15 --syzygy-path ~/tablebase/syzygy

Config file format (JSON):
{
    "engine_path": "/usr/local/bin/stockfish",
    "threads": 8,
    "hash_size": 8192,
    "skill_level": 20,
    "eval_depth": 20,
    "syzygy_path": "~/chess/syzygy"
}
        """,
    )

    parser.add_argument(
        "--engine-path",
        type=str,
        help="Path to Stockfish binary (default: /usr/games/stockfish)",
    )

    parser.add_argument(
        "--threads",
        type=int,
        help="Number of threads for engine to use (default: 4)",
    )

    parser.add_argument(
        "--hash-size", type=int, help="Hash table size in MB (default: 16384)"
    )

    parser.add_argument(
        "--skill-level",
        type=int,
        choices=range(0, 21),
        help="Engine skill level 0-20, where 20 is strongest (default: 20)",
    )

    parser.add_argument(
        "--depth",
        "--eval-depth",
        type=int,
        dest="eval_depth",
        help="Evaluation depth in plies (default: 18)",
    )

    parser.add_argument(
        "--syzygy-path",
        type=str,
        help="Path to Syzygy tablebase files (default: ~/chess/syzygy)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file with engine settings",
    )

    parser.add_argument(
        "--save-config",
        type=str,
        help="Save current settings to JSON config file and exit",
    )

    return parser


def load_config_file(config_path: str) -> dict[str, Any]:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, "r") as f:
            config_data = cast(dict[str, Any], load(f))

        valid_fields = set(
            EngineConfig.__dataclass_fields__.keys()
        )  # TODO: fix unresolved reference

        invalid_fields = set(config_data.keys()) - valid_fields

        if invalid_fields:
            print(
                f"Warning: Unknown config fields will be ignored: "
                f"{invalid_fields}"
            )

            config_data = {
                k: v for k, v in config_data.items() if k in valid_fields
            }

        return config_data

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")

    except JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")

    except Exception as e:  # TODO: handle specific exceptions
        raise ValueError(f"Error reading config file {config_path}: {e}")


def save_config_file(config: EngineConfig, config_path: str) -> None:
    """Save configuration to a JSON file."""
    try:
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            dump(asdict(config), f, indent=2)

        print(f"Configuration saved to: {config_path}")

    except Exception as e:
        raise ValueError(f"Error saving config file {config_path}: {e}")


def parse_config(args: Optional[list[str]] = None) -> EngineConfig:
    """Parse command-line arguments and config files to create final
    configuration.

    Args:
        args: Optional list of command-line arguments. If None, uses
            sys.argv.

    Returns:
        EngineConfig object with all settings resolved.

    Precedence order (highest to lowest):
    1. Command-line arguments
    2. Config file settings (if --config specified)
    3. Default values
    """
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    config = EngineConfig()

    if parsed_args.config:
        try:
            file_config = load_config_file(parsed_args.config)

            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration...")

    for key, value in vars(parsed_args).items():
        if value is not None and key not in ["config", "save_config"]:
            if hasattr(config, key):
                setattr(config, key, value)

    if parsed_args.save_config:
        save_config_file(config, parsed_args.save_config)
        exit(0)

    config.__post_init__()

    return config


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
    print(
        "Possible moves:\n"
        + "\n".join(
            f"{move.uci():5s}-> Eval score: {score}"
            + (f", Mate in {abs(mate_val)}" if mate_val else "")
            for move, (score, mate_val) in sorted_moves
        )
    )


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
    if tablebase:
        with suppress(IOError, ValueError, IndexError):
            wdl = tablebase.get_wdl(board)

            if wdl is not None:
                dtz = None

                with suppress(IOError, ValueError, IndexError):
                    dtz = tablebase.get_dtz(board)

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


EVAL_DEPTH = 18

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
    paths_to_check = [
        "/opt/homebrew/bin/stockfish",  # Apple Silicon Mac default
        "/usr/local/bin/stockfish",  # Intel Mac default
        "/opt/local/bin/stockfish",  # MacPorts location
        "/usr/bin/stockfish",  # Uncommon but possible
        "/usr/games/stockfish",  # Linux default
    ]

    with suppress(Exception):  # FIXME: too broad exception handling
        result = run(
            ["which", "stockfish"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0 and result.stdout.strip():
            filepath = result.stdout.strip()

            if path.exists(filepath) and access(filepath, X_OK):
                return True, filepath

        for filepath in paths_to_check:
            if path.exists(filepath) and access(filepath, X_OK):
                return True, filepath

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
    if path.exists(filepath):
        try:
            return open_tablebase(filepath)

        except Exception as e:  # TODO: handle specific exceptions
            print(f"Error loading Syzygy tablebases: {e}")
            return None

    print(f"Syzygy tablebases not found at {filepath}")
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
        board.pop()


def try_tablebase_evaluation(
    board: Board, tablebase: Tablebase | None
) -> (
    tuple[int | None, int | None] | None
):  # TODO: Refactor this to use lru_cache
    """Attempts to evaluate the position using the Syzygy tablebase.
    Returns (score, mate_value) tuple if successful, otherwise None.
    """
    if tablebase:
        try:
            wdl = tablebase.get_wdl(board)

        except (IOError, ValueError, IndexError):
            return None

        if wdl is not None:
            if wdl == 0:  # Draw
                return 0, None

            try:
                dtz_val = tablebase.get_dtz(board)

            except (IOError, ValueError, IndexError):
                return None

            mate_val = (
                dtz_val
                if wdl > 0
                else -dtz_val if dtz_val is not None else None
            )

            score = (
                (1000000 - (mate_val or 0))
                if wdl > 0
                else (-1000000 - (mate_val or 0))
            )

            if abs(mate_val or 0) >= 1000:
                mate_val = None

            return score, mate_val

        return None

    return None


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


def play_game(
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    move_history: list[chess.Move],
    tablebase: chess.syzygy.Tablebase | None = None,
    app_config: EngineConfig | None = None,
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
    board: chess.Board,
    engine: chess.engine.SimpleEngine,
    tablebase: chess.syzygy.Tablebase | None = None,
    app_config: EngineConfig | None = None,
) -> tuple[dict[chess.Move, tuple[int | None, int | None]], float]:
    """Evaluate moves and display them with timing information. Returns
    a tuple containing the moves evaluation dictionary and the time
    taken for the evaluation.
    """  # FIXME: mixes evaluation logic with display logic (wrong module)
    start_time = time()

    if tablebase:
        print_tablebase_info(board, tablebase)

    if app_config:
        eval_depth = app_config.eval_depth  # TODO: use ternary assignment

    else:
        eval_depth = get_dynamic_eval_depth(
            board
        )  # TODO: use ternary assignment

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
    moves_eval: dict[chess.Move, tuple[int | None, int | None]],
    is_white_turn: bool,
) -> list[tuple[chess.Move, tuple[int | None, int | None]]]:
    """Sorts the evaluated moves based on the score. Higher scores are
    better for White, lower scores are better for Black. Returns a list
    of tuples (Move, (score, mate_value)).
    """  # FIXME: wrong module (evaluation logic, not game logic)
    return sorted(
        list(moves_eval.items()), key=get_move_score, reverse=is_white_turn
    )


def get_move_score(
    item: tuple[chess.Move, tuple[int | None, int | None]],
) -> int:
    """Key function for sorting moves. Takes (Move, (score,
    mate_value)) and returns score for sorting.
    """  # FIXME: wrong module (evaluation logic, not game logic)
    return item[1][0] if item[1][0] is not None else 0


if __name__ == "__main__":
    main()
