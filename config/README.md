# Configuration System

The Stockfish-Analyzer scripts now support external configuration files to separate configuration from script logic.

## Configuration Files

### Engine Configuration (`config/example_config.json`)

Main application configuration including engine settings:

```json
{
  "engine_path": "/usr/games/stockfish",
  "threads": 4,
  "hash_size": 16384,
  "skill_level": 20,
  "eval_depth": 18,
  "syzygy_path": "~/chess/syzygy"
}
```

### Download Configuration (`config/download_config.json`)

Configuration for the Syzygy tablebase download script:

```json
{
  "syzygy_path": "~/chess/syzygy",
  "base_url": "https://tablebase.lichess.ovh/tables/standard/3-4-5",
  "download_3_piece": true,
  "download_4_piece": true,
  "download_5_piece": true,
  "confirm_overwrite": true
}
```

## Using the Scripts

### Setup Script

The setup script now accepts an optional configuration template:

```bash
# Use default template
./scripts/setup.sh

# Use custom template
./scripts/setup.sh config/my_template.json
```

The script will:
1. Load default values from the template file
2. Guide you through configuration options
3. Create a complete configuration file

### Download Script

The download script now accepts configuration file and target directory:

```bash
# Use default configuration
./scripts/download_syzygy.sh

# Use custom configuration
./scripts/download_syzygy.sh config/download_config.json

# Override target directory
./scripts/download_syzygy.sh config/download_config.json /my/custom/path
```

## Benefits

1. **Reusability**: Scripts can be used with different configurations
2. **Maintainability**: Configuration is separate from script logic
3. **Flexibility**: Easy to create multiple configurations for different environments
4. **Version Control**: Configuration files can be versioned and shared

## Migration

Existing hardcoded values have been moved to default configurations. The scripts remain backward compatible and will use sensible defaults if no configuration is provided.