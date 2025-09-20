from __future__ import annotations

import functools
import sys

from chess import Board, Move


@lru_cache(maxsize=None)
def from_uci(uci_str: str) -> Move:
    """Converts a UCI string to a chess Move object. Wraps
    Move.from_uci with error handling. Returns a Move object if
    successful, otherwise raises ValueError.
    """
    try:
        return Move.from_uci(uci_str)

    except (ValueError, IndexError):
        raise ValueError(f"Invalid UCI string: {uci_str}")


def parse_move_input(board: Board, user_input: str) -> Move | None:
    """Parse user input as a chess move. Tries SAN first, then UCI.
    Returns a Move object if successful, otherwise None.
    """
    try:
        return board.parse_san(user_input)

    except ValueError:
        try:
            return from_uci(user_input)

        except ValueError:
            return None


def handle_user_input(board: Board) -> Move | None:
    """Handles user input for making moves. Returns a valid Move object
    or None if the input is invalid.
    """
    user_input = input("Enter your move (UCI or SAN): ")

    # Handle special commands
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
