# Stockfish-Analyzer

Stockfish-Analyzer is a Python command-line chess analysis tool that provides
interactive gameplay with real-time Stockfish engine evaluation of all legal
moves. It features Unicode board display, centipawn scoring, mate detection,
progress tracking, and optional Syzygy tablebase support for perfect endgame
analysis.

**Always reference these instructions first and fallback to search or bash
commands only when you encounter unexpected information that does not match the
info here.**

## Working Effectively

### Initial Setup and Dependencies
- Install Python 3.8+ (tested with Python 3.12.3):
  - `python3 --version` - verify Python is available
- Install Python dependencies:
  - `python3 -m pip install -r requirements.txt` - installs chess~=1.11.2 and
    pytest~=8.4.2
- Install Stockfish chess engine:
  - **Ubuntu/Debian**: `sudo apt update && sudo apt install -y stockfish` -
    installs to `/usr/games/stockfish`
  - **macOS with Homebrew**: `brew install stockfish` - installs to
    `/opt/homebrew/bin/stockfish`
  - **Other systems**: Download from https://stockfishchess.org/ and update
    `ENGINE_PATH` in `src/engine_handler.py`

### Configure Engine Path
- **REQUIRED**: Edit `ENGINE_PATH` constant in `src/engine_handler.py` to point
  to your Stockfish binary
- Default macOS Homebrew path: `/opt/homebrew/bin/stockfish` (default in code)
- Default Ubuntu/Debian path: `/usr/games/stockfish`
- Verify engine works: `stockfish --help`
- **NOTE**: Application will fail with "No such file or directory" error if
  path is incorrect

### Testing and Validation
- Run test suite: `python3 -m pytest -v` - takes ~0.5 seconds, should show 39+
  passed tests
- Run type checking: `python3 -m mypy src/` - takes ~2 seconds, should show
  "Success: no issues found"
- **CRITICAL**: Always run both test suite and mypy before committing changes

### Running the Application
- **Standard run**: `python3 src/main.py` - starts interactive chess analysis
  session
- **From module**: `python3 -m src.main` - alternative way to run from repo
  root
- The application will:
  1. Display chess board in Unicode format with coordinates
  2. Show "Tablebases not available" or "Tablebases loaded" status
  3. Wait for move input (supports both SAN format like "e4", "Nf3+" and UCI
     format like "e2e4")
  4. Evaluate all legal moves with progress bar (can take 30+ seconds for
     complex positions)
  5. Display sorted move evaluations in centipawns or "Mate in N" format

### Optional Syzygy Tablebase Setup
- Download tablebases: `bash scripts/download_syzygy.sh` - downloads 3-5 piece
  endgame tables to `~/chess/syzygy`
- **WARNING**: Download is very large (several GB) and can take 30+ minutes
  depending on connection
- Tablebases provide instant perfect evaluation for endgame positions
- Default path: `~/chess/syzygy` (configurable via `SYZYGY_PATH` in
  `src/engine_handler.py`)

## Validation Scenarios

**ALWAYS** test these scenarios after making changes to ensure full
functionality:

### Basic Application Flow
1. `python3 src/main.py` - start application
2. Enter a legal move like "e4" and press Enter
3. Wait for move evaluation to complete (progress bar will show completion)
4. Verify move evaluations are displayed with scores in centipawns
5. Enter "quit" to exit cleanly

### Engine Integration Test
1. Run engine integration test:
   `python3 -c "import chess.engine; e = chess.engine.SimpleEngine.popen_uci('/path/to/stockfish'); print('Engine OK'); e.quit()"`
2. Replace `/path/to/stockfish` with your actual engine path
3. Should print "Engine OK" without errors

### Test Suite Validation
1. `python3 -m pytest -v` - run all tests
2. Verify most tests pass (some may skip if engine path is incorrect)
3. Check that no new test failures are introduced by your changes

## Engine Configuration and Performance

### Engine Settings (in `src/engine_handler.py`)
- **Threads**: 4 (configured in `get_engine()`)
- **Hash**: 16384 MB (16 GB hash table)
- **Skill Level**: 20 (maximum strength)
- **Evaluation Depth**: 18 plies (configurable via `EVAL_DEPTH`)

### Performance Expectations
- **Test suite**: ~0.5 seconds - NEVER CANCEL, set timeout to 60+ seconds for
  safety
- **Type checking**: ~2 seconds - NEVER CANCEL, set timeout to 60+ seconds for
  safety  
- **Move evaluation**: 30 seconds to 5+ minutes depending on position
  complexity and number of legal moves
- **Application startup**: ~1-2 seconds including engine initialization

### Known Limitations
- Move evaluation can be slow for complex positions (analyzing each move
  separately)
- Engine path is hardcoded (must be manually updated)
- No PGN export functionality (move history only prints to console)

## Repository Structure

### Key Source Files (`src/`)
- `main.py` - Entry point, orchestrates game flow
- `engine_handler.py` - Stockfish engine interface and move evaluation
  **[FREQUENTLY MODIFIED]**
- `game_logic.py` - Game state management and move processing **[FREQUENTLY
  MODIFIED]**
- `board_ui.py` - Unicode board display and progress reporting
- `input_handler.py` - Move parsing (SAN/UCI format conversion)

### Test Files (`test/`)
- `conftest.py` - Pytest fixtures including engine_path configuration **[CHECK
  AFTER ENGINE CHANGES]**
- `test_engine_handler.py` - Engine integration tests **[RUN AFTER ENGINE
  CHANGES]**
- `test_integration.py` - End-to-end application tests
- Complete test coverage for all modules with 43 total test cases

### Configuration Files
- `requirements.txt` - Python dependencies (chess, pytest)
- `mypy.ini` - Type checking configuration
- `.gitignore` - Standard Python/IDE exclusions

## Common Development Tasks

### After Changing Engine Configuration
1. Update `ENGINE_PATH` in `src/engine_handler.py`
2. Update `engine_path` fixture in `test/conftest.py` if needed
3. Update hardcoded paths in `test/test_integration.py` if needed
4. Run `python3 -m pytest test/test_engine_handler.py -v` to verify engine
tests pass
5. Test application startup: `python3 src/main.py` and try one move

### After Changing Game Logic
1. Run `python3 -m pytest test/test_game_logic.py -v`
2. Run full test suite: `python3 -m pytest -v`
3. Test complete user scenario: start app, make 2-3 moves, verify evaluations
   display correctly

### After Changing UI/Display Code
1. Run `python3 -m pytest test/test_board_ui.py -v`
2. Test visual output: `python3 src/main.py` and verify board displays
   correctly with proper Unicode pieces
3. Test progress bar display by making a move and watching evaluation progress

### Before Committing Changes
1. **MANDATORY**: `python3 -m pytest -v` - all tests must pass or maintain
   existing skip count
2. **MANDATORY**: `python3 -m mypy src/` - must show "Success: no issues found"
3. **MANDATORY**: `black -l79 src/*.py; black -l79 test/*.py;  isort src/*.py; isort test/*.py;  mypy --strict src/*.py; mypy --strict test/*.py; flake8 src/*.py; flake8 test/*.py; pytest;` - code formatting and linting checks
4. **RECOMMENDED**: Test one complete application scenario manually

## Troubleshooting

### "Stockfish engine not found" Errors
- **FileNotFoundError**: `[Errno 2] No such file or directory:
  '/opt/homebrew/bin/stockfish'`
  - This is EXPECTED on fresh clone - update `ENGINE_PATH` in
    `src/engine_handler.py`
- **Test failures**: "Stockfish engine not found. Skipping tests."
  - Update `engine_path` fixture in `test/conftest.py` to match your system
  - Update hardcoded paths in `test/test_integration.py` 
- Verify Stockfish installation: `which stockfish` or check expected path
- Common paths:
  - Ubuntu/Debian: `/usr/games/stockfish`
  - macOS Homebrew: `/opt/homebrew/bin/stockfish`
  - Windows: `C:\path\to\stockfish.exe`

### Import Errors
- Ensure you're running from repository root directory
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Check Python version: `python3 --version` (requires 3.8+)

### Slow Performance During Development
- Use shorter evaluation depth: temporarily reduce `EVAL_DEPTH` in
  `src/engine_handler.py`
- Skip tablebase download during development (large files, not required for
  basic functionality)
- Some positions naturally take longer to evaluate (especially opening
  positions with many legal moves)

## Quick Reference Commands

```bash
# Setup from fresh clone
python3 --version                            # Verify Python 3.8+
python3 -m pip install -r requirements.txt   # Install dependencies
sudo apt install stockfish                   # Ubuntu - install engine
# REQUIRED: Update ENGINE_PATH in src/engine_handler.py to match your system

# Development workflow  
python3 -m pytest -v                         # Run tests (~0.5 sec)
python3 -m mypy src/                         # Type check (~2 sec)
python3 src/main.py                          # Run application
python3 -m src.main                          # Alternative way to run

# Optional tablebase setup (large download)
bash scripts/download_syzygy.sh              # Download endgame tables
```
