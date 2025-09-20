import chess

try:
    import board_ui
    import engine_handler
    import game_logic

except ImportError:
    import src.board_ui as board_ui
    import src.engine_handler as engine_handler
    import src.game_logic as game_logic


def main() -> None:
    """Main function to run the interactive chess game."""
    board = chess.Board()
    move_history: list[chess.Move] = []
    engine = engine_handler.get_engine(engine_handler.ENGINE_PATH)
    tablebase = engine_handler.get_syzygy_tablebase()

    print("Tablebases loaded" if tablebase else "Tablebases not available")

    try:
        src.game_logic.play_game(board, engine, move_history, tablebase)
        src.board_ui.print_game_over_info(board, move_history)

        if tablebase:
            src.board_ui.print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


if __name__ == "__main__":
    main()
