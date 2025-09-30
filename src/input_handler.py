from __future__ import annotations

import sys

import chess


def parse_move_input(board: chess.Board, user_input: str) -> chess.Move | None:
    """Parse user input as a chess move. Tries SAN first, then UCI.
    Returns a Move object if successful, otherwise None.
    """
    try:
        return board.parse_san(user_input)

    except ValueError:
        try:
            return chess.Move.from_uci(user_input)

        except ValueError:
            return None


def handle_user_input(board: chess.Board) -> chess.Move | None:
    """Handles user input for making moves. Returns a valid Move object
    or None if the input is invalid.
    """
    user_input = input("Enter your move (UCI or SAN): ")
    return process_user_input(board, user_input)


def process_user_input(
    board: chess.Board, user_input: str
) -> chess.Move | None:
    """Processes a user input string and returns a valid Move object
    or None if the input is invalid. Separated from handle_user_input
    for better testability.
    """
    if user_input.lower() in ["quit", "q", "exit"]:
        print("Exiting game...")
        sys.exit(0)

    move = parse_move_input(board, user_input)

    if move is None:
        print("Invalid move format. Please try again.\n")
        return None

    if move not in board.legal_moves:
        print("Illegal move. Please try again.\n")
        return None

    return move
