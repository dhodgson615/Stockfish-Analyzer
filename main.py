from chess import Board, Move

from board_ui import print_game_over_info, print_tablebase_info
from engine_handler import ENGINE_PATH, get_engine, get_syzygy_tablebase
from game_logic import play_game


def main() -> None:
    """Main function to run the interactive chess game."""
    board = Board()
    move_history: list[Move] = []  # Explicit Move type

    engine = get_engine(ENGINE_PATH)
    tablebase = get_syzygy_tablebase()

    print("Tablebases loaded" if tablebase else "Tablebases not available")

    try:
        play_game(board, engine, move_history, tablebase)
        print_game_over_info(board, move_history)

        if tablebase:
            print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


if __name__ == "__main__":
    main()
