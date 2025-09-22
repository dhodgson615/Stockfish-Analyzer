# Docker Setup for Stockfish-Analyzer

This directory contains Docker configuration files for running Stockfish-Analyzer in a containerized environment.

## Quick Start

### Building the Image

```bash
docker build -t stockfish-analyzer .
```

### Running the Container

#### Basic Usage
```bash
docker run -it stockfish-analyzer
```

This will start the application with the default example configuration.

#### Using Custom Configuration
```bash
# Mount your config directory
docker run -it -v $(pwd)/config:/app/config stockfish-analyzer python3 src/main.py --config config/my_config.json
```

#### With Syzygy Tablebases
```bash
# Mount tablebase directory (if you have downloaded tablebases)
docker run -it -v $(pwd)/syzygy:/app/syzygy stockfish-analyzer
```

#### Interactive Development Mode
```bash
# Mount source code for development
docker run -it -v $(pwd):/app stockfish-analyzer bash
```

## Configuration

### Default Configuration
The container uses `/app/config/example_config.json` by default, which configures:
- Engine path: `/usr/games/stockfish` (pre-installed in container)
- 4 threads
- 16GB hash size
- Skill level 20 (maximum)
- Evaluation depth 18

### Custom Configuration
1. Create your configuration file in the `config/` directory
2. Mount the config directory when running: `-v $(pwd)/config:/app/config`
3. Specify your config: `--config config/your_config.json`

### Environment Variables
- `STOCKFISH_PATH`: Path to Stockfish binary (default: `/usr/games/stockfish`)
- `PYTHONPATH`: Python module search path (default: `/app`)

## Syzygy Tablebases

To use Syzygy endgame tablebases:

1. Download tablebases to your host system:
   ```bash
   ./scripts/download_syzygy.sh config/download_config.json ./syzygy
   ```

2. Mount the tablebase directory:
   ```bash
   docker run -it -v $(pwd)/syzygy:/app/syzygy stockfish-analyzer
   ```

## Testing

Run tests inside the container:
```bash
docker run --rm stockfish-analyzer python3 -m pytest -v
```

Run type checking:
```bash
docker run --rm stockfish-analyzer python3 -m mypy src/
```

## Multi-Platform Support

The Docker image is built on `python:3.12-slim` which supports multiple architectures:
- Linux AMD64 (x86_64)
- Linux ARM64 (aarch64)
- Linux ARM/v7

Build for specific platform:
```bash
docker build --platform linux/amd64 -t stockfish-analyzer .
```

## Security

- Runs as non-root user `chessuser` (UID 1000)
- Minimal base image with only required dependencies
- No network access required for basic functionality

## Troubleshooting

### Engine Not Found
If you get "Stockfish engine not found" errors:
1. Verify Stockfish is installed: `docker run stockfish-analyzer which stockfish`
2. Check the configuration points to `/usr/games/stockfish`

### Permission Issues
If you have permission issues with mounted volumes:
```bash
# Ensure your local files are readable by UID 1000
sudo chown -R 1000:1000 config/ syzygy/
```

### Memory Issues
For large analysis sessions, increase Docker memory:
```bash
docker run -m 4g stockfish-analyzer  # Allocate 4GB RAM
```