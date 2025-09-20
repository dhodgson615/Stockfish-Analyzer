import chess

try:
    import board_ui
    import config
    import engine_handler
    import game_logic

except ImportError:
    import src.board_ui as board_ui
    import src.config as config
    import src.engine_handler as engine_handler
    import src.game_logic as game_logic


def main() -> None:
    """Main function to run the interactive chess game."""
    # Parse configuration from CLI args and config files
    app_config = config.parse_config()

    # Display configuration summary
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
        game_logic.play_game(board, engine, move_history, tablebase, app_config)
        board_ui.print_game_over_info(board, move_history)

        if tablebase:
            board_ui.print_tablebase_info(board, tablebase)

    finally:
        engine.quit()

        if tablebase:
            tablebase.close()


if __name__ == "__main__":
    main()
