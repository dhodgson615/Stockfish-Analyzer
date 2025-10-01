import chess

__all__ = [
    "config",
    "engine_handler",
    "game_logic",
    "board_ui",
    "main",
]

try:
    import board_ui
    import engine_handler
    import game_logic

    print(
        "Imported board_ui, engine_handler, and game_logic from the first try block"
    )

except ImportError:
    try:
        import src.board_ui as board_ui
        import src.engine_handler as engine_handler
        import src.game_logic as game_logic

        print(
            "Imported board_ui, engine_handler, and game_logic from the except block"
        )

    except ImportError:
        import board_ui
        import engine_handler
        import game_logic

        print(
            "Imported board_ui, engine_handler, and game_logic from the last except block"
        )

try:
    from . import config

    print("Imported config from the first try block")

except ImportError:
    try:
        import config

        print("Imported config from the except block")

    except ImportError:
        import src.config as config

        print("Imported config from the last except block")


def main() -> None:
    """Main function to run the interactive chess game."""
    app_config = config.parse_config()
    print(f"Engine: {app_config.engine_path}")

    print(
        f"Threads: {app_config.threads}, Hash: {app_config.hash_size}MB, "
        f"Skill: {app_config.skill_level}, Depth: {app_config.eval_depth}"
    )

    board = chess.Board()
    move_history: list[chess.Move] = []

    # Initialize engine with configuration
    engine = engine_handler.get_engine(
        engine_path=app_config.engine_path,
        threads=app_config.threads,
        hash_size=app_config.hash_size,
        skill_level=app_config.skill_level,
    )

    # Initialize tablebase with configuration
    tablebase = engine_handler.get_syzygy_tablebase(app_config.syzygy_path)
    print("Tablebases loaded" if tablebase else "Tablebases not available")

    try:
        # Pass configuration to game logic for evaluation depth
        game_logic.play_game(
            board, engine, move_history, tablebase, app_config
        )

        board_ui.print_game_over_info(board, move_history)

        if tablebase:
            board_ui.print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


if __name__ == "__main__":
    main()
