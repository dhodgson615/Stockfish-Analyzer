#!/bin/bash

# Syzygy Tablebase Download Script
# Downloads 3-5 piece endgame tablebases for Stockfish
# Usage: download_syzygy.sh [config_file] [target_directory]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_SYZYGY_PATH="$HOME/chess/syzygy"
DEFAULT_BASE_URL="https://tablebase.lichess.ovh/tables/standard/3-4-5"
DEFAULT_CONFIG_PATH="config/download_config.json"

# Function to load configuration from JSON file
load_config() {
    local config_file="$1"
    
    if [[ -f "$config_file" ]]; then
        echo -e "${BLUE}Loading configuration from: $config_file${NC}"
        
        # Extract values using python3 (more reliable than shell JSON parsing)
        if command -v python3 >/dev/null 2>&1; then
            SYZYGY_PATH=$(python3 -c "import json; config=json.load(open('$config_file')); print(config.get('syzygy_path', '$DEFAULT_SYZYGY_PATH'))" 2>/dev/null || echo "$DEFAULT_SYZYGY_PATH")
            BASE_URL=$(python3 -c "import json; config=json.load(open('$config_file')); print(config.get('base_url', '$DEFAULT_BASE_URL'))" 2>/dev/null || echo "$DEFAULT_BASE_URL")
        else
            echo -e "${YELLOW}Warning: python3 not found, using default configuration${NC}"
            SYZYGY_PATH="$DEFAULT_SYZYGY_PATH"
            BASE_URL="$DEFAULT_BASE_URL"
        fi
    else
        echo -e "${YELLOW}Config file not found: $config_file${NC}"
        echo -e "${YELLOW}Using default configuration${NC}"
        SYZYGY_PATH="$DEFAULT_SYZYGY_PATH"
        BASE_URL="$DEFAULT_BASE_URL"
    fi
    
    # Expand tilde in path
    SYZYGY_PATH="${SYZYGY_PATH/#\~/$HOME}"
}

# Parse command line arguments
CONFIG_FILE="$DEFAULT_CONFIG_PATH"
TARGET_DIR=""

if [[ $# -ge 1 ]]; then
    CONFIG_FILE="$1"
fi

if [[ $# -ge 2 ]]; then
    TARGET_DIR="$2"
fi

echo -e "${BLUE}=== Syzygy Tablebase Downloader ===${NC}"
echo "Downloading 3-5 piece endgame tablebases..."
echo

# Load configuration
load_config "$CONFIG_FILE"

# Override target directory if specified
if [[ -n "$TARGET_DIR" ]]; then
    SYZYGY_PATH="$TARGET_DIR"
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Target directory: $SYZYGY_PATH"
echo "  Base URL: $BASE_URL"
echo

# Check if path already exists and has content
if [[ -d "$SYZYGY_PATH" ]] && [[ "$(ls -A "$SYZYGY_PATH" 2>/dev/null)" ]]; then
    echo -e "${YELLOW}Warning: Directory $SYZYGY_PATH already contains files.${NC}"
    read -p "Continue anyway? [y/N]: " response
    if [[ ! "${response,,}" =~ ^(y|yes)$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create directory if it doesn't exist
echo -e "${YELLOW}Creating directory: $SYZYGY_PATH${NC}"
mkdir -p "$SYZYGY_PATH"
cd "$SYZYGY_PATH"

# List of all 3-4-5 piece tablebase files
FILES=(
    "K-v-K.rtbw"    "K-v-K.rtbz"
    "KBN-v-K.rtbw"  "KBN-v-K.rtbz"
    "KBP-v-K.rtbw"  "KBP-v-K.rtbz"
    "KBP-v-KB.rtbw" "KBP-v-KB.rtbz"
    "KB-v-K.rtbw"   "KB-v-K.rtbz"
    "KB-v-KB.rtbw"  "KB-v-KB.rtbz"
    "KB-v-KN.rtbw"  "KB-v-KN.rtbz"
    "KN-v-K.rtbw"   "KN-v-K.rtbz"
    "KN-v-KN.rtbw"  "KN-v-KN.rtbz"
    "KP-v-K.rtbw"   "KP-v-K.rtbz"
    "KP-v-KP.rtbw"  "KP-v-KP.rtbz"
    "KQ-v-K.rtbw"   "KQ-v-K.rtbz"
    "KQ-v-KB.rtbw"  "KQ-v-KB.rtbz"
    "KQ-v-KN.rtbw"  "KQ-v-KN.rtbz"
    "KQ-v-KP.rtbw"  "KQ-v-KP.rtbz"
    "KQ-v-KQ.rtbw"  "KQ-v-KQ.rtbz"
    "KQ-v-KR.rtbw"  "KQ-v-KR.rtbz"
    "KR-v-K.rtbw"   "KR-v-K.rtbz"
    "KR-v-KB.rtbw"  "KR-v-KB.rtbz"
    "KR-v-KN.rtbw"  "KR-v-KN.rtbz"
    "KR-v-KP.rtbw"  "KR-v-KP.rtbz"
    "KR-v-KR.rtbw"  "KR-v-KR.rtbz"
)

echo -e "${YELLOW}Downloading tablebase files...${NC}"
for file in "${FILES[@]}"; do
    echo "Downloading $file..."
    if ! curl -f -o "$file" "$BASE_URL/$file"; then
        echo -e "${RED}Failed to download $file${NC}"
        echo -e "${YELLOW}Continuing with remaining files...${NC}"
    fi
done

echo
echo -e "${GREEN}Download complete! Tablebases are now available at: $SYZYGY_PATH${NC}"
echo -e "${BLUE}You can now use these tablebases with Stockfish-Analyzer${NC}"

