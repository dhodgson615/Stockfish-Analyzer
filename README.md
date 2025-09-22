# Stockfish-Analyzer

This project is a lightweight command-line tool that lets you play through a
chess game while Stockfish evaluates every legal move for the side to move. It
is ideal for learning, blunder-checking, or simply exploring engine lines
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
- Syzygy endgame tablebase support for instant evaluation of 3-5 piece endings
  (if installed)

## Engine Configuration

The Stockfish engine is configured with:
- 4 threads
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

## Docker Support

For the easiest setup, you can use Docker which includes all dependencies:

```bash
# Build and run with Docker
docker build -t stockfish-analyzer .
docker run -it stockfish-analyzer

# Or use Docker Compose
docker-compose up stockfish-analyzer
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions and configuration options.

## Syzygy Tablebase Support (Optional)

To enable instant endgame evaluation for 3-5 piece positions, download the
Syzygy tablebases:

```bash
bash download_syzygy.sh
```

This will install the tablebases to `~/chess/syzygy` (the default path used by
the script).

## Quick Start

### Method 1: First-Time Setup (Recommended)

For first-time users, run the interactive setup script that will help you install Stockfish and optionally download tablebases:

```bash
scripts/setup.sh
```

This script will:
- Detect or help install Stockfish engine on your system
- Optionally download Syzygy tablebases for perfect endgame analysis
- Create a configuration file with the detected paths
- Test the installation to ensure everything works

Once setup is complete, run the analyzer with your configuration:

```bash
python3 src/main.py --config config/stockfish_config.json
```

### Method 2: Using Command Line Arguments

Run the script with your preferred settings:

```bash
# Basic usage with default settings
python3 src/main.py

# Custom engine path and performance settings
python3 src/main.py --engine-path /usr/local/bin/stockfish --threads 8 --hash-size 8192

# Adjust engine strength and evaluation depth
python3 src/main.py --skill-level 15 --depth 12

# Custom tablebase location
python3 src/main.py --syzygy-path /my/tablebase/path
```

### Method 3: Using Configuration Files

1. Create a configuration file:

```bash
python3 src/main.py --threads 8 --depth 20 --save-config my_config.json
```

2. Use the configuration file:

```bash
python3 src/main.py --config my_config.json
```

### Method 4: Legacy Method (Still Supported)

1. Edit the `ENGINE_PATH` constant in `engine_handler.py` so it points to your
Stockfish executable.

Example macOS Homebrew path: `/opt/homebrew/bin/stockfish`

2. Run the script:

```bash
python3 src/main.py
```

### Command Line Options

- `--engine-path`: Path to Stockfish binary (default: /usr/games/stockfish)
- `--threads`: Number of threads (default: 4)  
- `--hash-size`: Hash table size in MB (default: 16384)
- `--skill-level`: Engine skill 0-20, where 20 is strongest (default: 20)
- `--depth`: Evaluation depth in plies (default: 18)
- `--syzygy-path`: Path to Syzygy tablebase files (default: ~/chess/syzygy)
- `--config`: Load settings from JSON config file
- `--save-config`: Save current settings to JSON file and exit

For complete usage information: `python3 src/main.py --help`

### Gameplay

When it is your turn, type a move (SAN or UCI) and press Enter. The engine
will re-evaluate the new position and show fresh advice.

Play until checkmate, stalemate, or another terminal condition; the script
then prints the final board, move list, and winner/draw result.

## Known Limitations

- Slow for complex positions: analysing each move separately restarts the
  search each time. Multipv or a single engine.play() search would be faster.
- No PGN export: move history prints to console only.

## Future Enhancements

The following features are planned for future releases:

- Refactored move sorting logic
- More specific exception handling
- Unit tests for core functionalities
- Improved user interface
- Performance optimizations
- Optional GUI support
- Logging for better debugging

## License

This code is released under the MIT License. Stockfish itself is GPLv3; be sure
to follow its terms when redistributing the binary.

## Acknowledgements

[python-chess](https://python-chess.readthedocs.io/en/latest/) by Niklas Fiekas

[Stockfish](https://stockfishchess.org) - the strongest open-source chess
engine

[Syzygy tablebases](https://syzygy-tables.info) - for perfect endgame analysis
