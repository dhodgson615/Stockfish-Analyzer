# Stockfish-Analyzer

This project is a lightweight command-line tool that lets you play through a
chess game while Stockfish evaluates every legal move for the side to move.
It is ideal for learning, blunder-checking, or simply exploring engine lines
without a full-blown GUI.

## Key Features

- Unicode board display with borders for easy reading in any terminal
- Fixed-depth evaluation (default 12 plies) of every legal move, reported in
  centipawns and, when applicable, "Mate in N"
- Progress bar with real-time "time remaining" estimate
- Sorted move list from the point of view of the side to move
- Accepts moves in both SAN (`e4`, `Nf3+`, …) and UCI (`e2e4`, `g1f3`, …)
  formats
- Graceful end-of-game summary with move history and final result
- Clean quit of the Stockfish engine even on exceptions

## Engine Configuration

The Stockfish engine is configured with:
- 2 threads
- 16384 MB hash size
- Skill Level 20 (maximum strength)

## Prerequisites

- Python 3.8+ (tested up to 3.12)
- [`python-chess`](https://pypi.org/project/python-chess/) library
- A working Stockfish binary available on your system

Install the Python dependency with:

```bash
pip3 install python-chess
```

## Quick Start

1. Edit the `engine_path` variable near the top of main() so it points to your
Stockfish executable.

   Example macOS Homebrew path: `/opt/homebrew/bin/stockfish`
2. Run the script:
   ```bash
   python3 main.py
   ```

3. When it is your turn, type a move (SAN or UCI) and press **Enter**. The
   engine will re-evaluate the new position and show fresh advice.

4. Play until checkmate, stalemate, or another terminal condition; the script
   then prints the final board, move list, and winner/draw result.

---

## Known Limitations
- **Slow for complex positions**: analysing each move separately restarts the
  search each time. Multipv or a single `engine.play()` search would be faster.
- **Hard-coded engine path**: update the string or add CLI args/env vars.
- **No PGN export**: move history prints to console only.
- **No endgame tablebase support**: engame positions are redundantly calculated.

---

## License
This code is released under the MIT License. Stockfish itself is GPLv3; be sure
to follow its terms when redistributing the binary.

---

## Acknowledgements
- [python-chess](https://github.com/niklasf/python-chess) by Niklas Fiekas

- [Stockfish](https://stockfishchess.org/) - the strongest open-source chess
  engine
