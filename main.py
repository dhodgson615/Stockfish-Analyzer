"""Script that allows a user to play chess against themselves with move
evaluations provided by a chess engine and Syzygy tablebases. The script
displays the chess board, evaluates possible moves, and handles user input
for moves. It also shows game over information including the move history and
result."""

"""TODO:
    - Make exception handling more specific
    - Add configurable engine settings
    - Add logging for better debugging and tracking
    - Add images to README for better documentation
    - Add graphs to visualize move evaluations over time
"""

from chess import Board

from board_ui import print_game_over_info, print_tablebase_info
from engine_handler import ENGINE_PATH, get_engine, get_syzygy_tablebase
from game_logic import play_game


def main() -> None:
    """Main function to run the interactive chess game."""
    board = Board()
    move_history = []

    # Initialize the chess engine
    engine = get_engine(ENGINE_PATH)

    # Initialize Syzygy tablebases if available
    tablebase = get_syzygy_tablebase()
    
    if tablebase:
        print(f"Syzygy tablebases loaded")
    else:
        print("Syzygy tablebases not available")

    try:
        play_game(board, engine, move_history, tablebase)
        print_game_over_info(board, move_history)

        # Display final tablebase info if applicable
        if tablebase:
            print_tablebase_info(board, tablebase)
    finally:
        engine.quit()
        if tablebase:
            tablebase.close()


if __name__ == "__main__":
    main()
