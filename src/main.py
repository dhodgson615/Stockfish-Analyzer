import chess

import src.board_ui
import src.engine_handler
import src.game_logic


def main() -> None:
    """Main function to run the interactive chess game."""
    board = chess.Board()
    move_history: list[chess.Move] = []
    engine = src.engine_handler.get_engine(src.engine_handler.ENGINE_PATH)
    tablebase = src.engine_handler.get_syzygy_tablebase()

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
