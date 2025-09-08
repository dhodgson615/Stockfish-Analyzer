"""Script that allows a user to play chess against themselves with move
evaluations provided by a chess engine. The script displays the chess
board, evaluates possible moves, and handles user input for moves. It
also shows game over information including the move history and
result."""

"""TODO:
    - Make exception handling more specific
    - Add unit tests for core functionalities
    - Add Sygygy support for more efficient endgame evaluations
    - Improve user interface for better experience
    - Optimize performance for faster move evaluations
    - Add GUI support for a more interactive experience
    - Add configurable engine settings
    - Add logging for better debugging and tracking
    - Add images to README for better documentation
    - Add graphs to visualize move evaluations over time
"""

from chess import Board

from board_ui import print_game_over_info
from engine_handler import ENGINE_PATH, get_engine
from game_logic import play_game


def main() -> None:
    """Main function to run the interactive chess game."""
    board = Board()
    move_history = []
    engine = get_engine(ENGINE_PATH)

    try:
        play_game(board, engine, move_history)
        print_game_over_info(board, move_history)
    finally:
        engine.quit()


if __name__ == "__main__":
    main()
