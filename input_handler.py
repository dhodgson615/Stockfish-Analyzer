from chess import Board, Move


def from_uci(uci_str: str) -> Move:
    """Converts a UCI string to a chess Move object. Wraps
    Move.from_uci with error handling.
    """
    try:
        return Move.from_uci(uci_str)
    except (ValueError, IndexError):
        raise ValueError(f"Invalid UCI string: {uci_str}")


def parse_move_input(board: Board, user_input: str) -> Move | None:
    """Parse user input as a chess move."""
    try:
        return board.parse_san(user_input)
    except ValueError:
        try:
            return from_uci(user_input)
        except (ValueError, IndexError):
            print("Invalid move format. Please try again.\n")
            return None


def handle_user_input(board: Board) -> Move | None:
    """Handles user input for the next move."""
    color = "White" if board.turn else "Black"
    user_input = input(
        f"Enter the next move for {color} (SAN or UCI): "
    ).strip()

    move = parse_move_input(board, user_input)
    if not move:
        return None

    if move not in board.legal_moves:
        print("Illegal move. Please try again.\n")
        return None

    return move
