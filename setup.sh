#!/bin/bash

# Stockfish-Analyzer Setup Script
# Configures engine and downloads tablebases via CLI prompts

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default paths
DEFAULT_SYZYGY_PATH="$HOME/chess/syzygy"
DEFAULT_CONFIG_PATH="stockfish_config.json"

echo -e "${BLUE}=== Stockfish-Analyzer Setup ===${NC}"
echo "This script will help you configure Stockfish engine and optionally download tablebases."
echo

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to find existing Stockfish installation
find_stockfish() {
    local paths=(
        "/opt/homebrew/bin/stockfish"    # Apple Silicon Mac
        "/usr/local/bin/stockfish"       # Intel Mac
        "/opt/local/bin/stockfish"       # MacPorts
        "/usr/bin/stockfish"             # Linux alternative
        "/usr/games/stockfish"           # Linux default
    )
    
    # Try 'which' first
    if command_exists stockfish; then
        local which_result=$(which stockfish 2>/dev/null)
        if [[ -n "$which_result" && -x "$which_result" ]]; then
            echo "$which_result"
            return 0
        fi
    fi
    
    # Check predefined paths
    for path in "${paths[@]}"; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Function to install Stockfish on different systems
install_stockfish() {
    local os=$(detect_os)
    
    echo -e "${YELLOW}Installing Stockfish chess engine...${NC}"
    
    case $os in
        "macos")
            if command_exists brew; then
                echo "Installing via Homebrew..."
                brew install stockfish
            else
                echo -e "${RED}Error: Homebrew not found.${NC}"
                echo "Please install Homebrew first: https://brew.sh/"
                echo "Or install Stockfish manually from: https://stockfishchess.org/"
                return 1
            fi
            ;;
        "linux")
            echo "Attempting to install via apt (requires sudo)..."
            if sudo apt update && sudo apt install -y stockfish; then
                echo -e "${GREEN}Stockfish installed successfully!${NC}"
            else
                echo -e "${RED}Failed to install via apt.${NC}"
                echo "Please install Stockfish manually:"
                echo "  - Ubuntu/Debian: sudo apt install stockfish"
                echo "  - Download from: https://stockfishchess.org/"
                return 1
            fi
            ;;
        *)
            echo -e "${RED}Unsupported OS. Please install Stockfish manually.${NC}"
            echo "Download from: https://stockfishchess.org/"
            return 1
            ;;
    esac
}

# Function to test Stockfish installation
test_stockfish() {
    local stockfish_path="$1"
    
    echo -e "${YELLOW}Testing Stockfish installation...${NC}"
    
    if [[ ! -x "$stockfish_path" ]]; then
        echo -e "${RED}Error: Stockfish not found at $stockfish_path${NC}"
        return 1
    fi
    
    # Test if Stockfish responds correctly
    if echo "quit" | "$stockfish_path" >/dev/null 2>&1; then
        echo -e "${GREEN}Stockfish test successful!${NC}"
        return 0
    else
        echo -e "${RED}Error: Stockfish test failed${NC}"
        return 1
    fi
}

# Function to download tablebases
download_tablebases() {
    local syzygy_path="$1"
    
    echo -e "${YELLOW}Downloading Syzygy tablebases...${NC}"
    echo "This may take several minutes and requires several GB of space."
    
    # Create directory
    mkdir -p "$syzygy_path"
    
    # Use existing download script if available
    if [[ -f "scripts/download_syzygy.sh" ]]; then
        echo "Using existing download script..."
        # Modify the script to use custom path
        sed "s|~/chess/syzygy|$syzygy_path|g" scripts/download_syzygy.sh > /tmp/download_syzygy_custom.sh
        chmod +x /tmp/download_syzygy_custom.sh
        /tmp/download_syzygy_custom.sh
        rm /tmp/download_syzygy_custom.sh
    else
        echo -e "${RED}Error: Download script not found${NC}"
        return 1
    fi
}

# Function to create configuration file
create_config() {
    local stockfish_path="$1"
    local syzygy_path="$2"
    local config_path="$3"
    
    echo -e "${YELLOW}Creating configuration file: $config_path${NC}"
    
    cat > "$config_path" << EOF
{
    "engine_path": "$stockfish_path",
    "threads": 4,
    "hash_size": 16384,
    "skill_level": 20,
    "eval_depth": 18,
    "syzygy_path": "$syzygy_path"
}
EOF
    
    echo -e "${GREEN}Configuration saved to: $config_path${NC}"
}

# Function to get user input with default
get_input() {
    local prompt="$1"
    local default="$2"
    local response
    
    if [[ -n "$default" ]]; then
        read -p "$prompt [$default]: " response
        echo "${response:-$default}"
    else
        read -p "$prompt: " response
        echo "$response"
    fi
}

# Function to get yes/no input
get_yes_no() {
    local prompt="$1"
    local default="$2"
    local response
    
    while true; do
        if [[ -n "$default" ]]; then
            read -p "$prompt [y/n, default: $default]: " response
            response="${response:-$default}"
        else
            read -p "$prompt [y/n]: " response
        fi
        
        case "${response,,}" in
            y|yes) return 0 ;;
            n|no) return 1 ;;
            *) echo "Please answer y or n." ;;
        esac
    done
}

# Main setup flow
main() {
    local stockfish_path=""
    local syzygy_path=""
    local config_path=""
    
    # Check for existing Stockfish
    echo -e "${BLUE}Step 1: Stockfish Engine Setup${NC}"
    if stockfish_path=$(find_stockfish); then
        echo -e "${GREEN}Found existing Stockfish at: $stockfish_path${NC}"
        if get_yes_no "Use this installation?" "y"; then
            if test_stockfish "$stockfish_path"; then
                echo -e "${GREEN}Using existing Stockfish installation.${NC}"
            else
                echo -e "${RED}Existing installation failed test.${NC}"
                stockfish_path=""
            fi
        else
            stockfish_path=""
        fi
    fi
    
    # Install Stockfish if needed
    if [[ -z "$stockfish_path" ]]; then
        if get_yes_no "Stockfish not found or test failed. Install now?" "y"; then
            if install_stockfish; then
                # Try to find it again after installation
                if stockfish_path=$(find_stockfish); then
                    if test_stockfish "$stockfish_path"; then
                        echo -e "${GREEN}Stockfish installation successful!${NC}"
                    else
                        echo -e "${RED}Installation completed but test failed.${NC}"
                        exit 1
                    fi
                else
                    echo -e "${RED}Installation completed but Stockfish not found.${NC}"
                    echo "Please check the installation and run this script again."
                    exit 1
                fi
            else
                echo -e "${RED}Failed to install Stockfish.${NC}"
                echo "Please install manually and run this script again."
                exit 1
            fi
        else
            echo -e "${YELLOW}Skipping Stockfish installation.${NC}"
            echo "You'll need to install it manually and update the configuration."
            # Use a placeholder path
            stockfish_path="/usr/games/stockfish"
        fi
    fi
    
    # Tablebase setup
    echo
    echo -e "${BLUE}Step 2: Syzygy Tablebase Setup${NC}"
    echo "Syzygy tablebases provide perfect endgame analysis but require several GB of space."
    
    if get_yes_no "Download Syzygy tablebases?" "n"; then
        syzygy_path=$(get_input "Installation path" "$DEFAULT_SYZYGY_PATH")
        
        if [[ -d "$syzygy_path" && -n "$(ls -A "$syzygy_path" 2>/dev/null)" ]]; then
            echo -e "${YELLOW}Directory $syzygy_path already contains files.${NC}"
            if ! get_yes_no "Continue with download?" "n"; then
                echo "Skipping tablebase download."
                syzygy_path=""
            fi
        fi
        
        if [[ -n "$syzygy_path" ]]; then
            if download_tablebases "$syzygy_path"; then
                echo -e "${GREEN}Tablebase download completed!${NC}"
            else
                echo -e "${RED}Tablebase download failed.${NC}"
                syzygy_path=""
            fi
        fi
    else
        echo "Skipping tablebase download."
        syzygy_path=""
    fi
    
    # Configuration file creation
    echo
    echo -e "${BLUE}Step 3: Configuration File${NC}"
    config_path=$(get_input "Save configuration to" "$DEFAULT_CONFIG_PATH")
    
    # Use default path if user doesn't want tablebases
    local final_syzygy_path="${syzygy_path:-$DEFAULT_SYZYGY_PATH}"
    
    create_config "$stockfish_path" "$final_syzygy_path" "$config_path"
    
    # Final instructions
    echo
    echo -e "${GREEN}=== Setup Complete! ===${NC}"
    echo
    echo "To run Stockfish-Analyzer with your configuration:"
    echo -e "${BLUE}  python3 src/main.py --config $config_path${NC}"
    echo
    echo "Or use individual command-line options:"
    echo -e "${BLUE}  python3 src/main.py --engine-path '$stockfish_path'${NC}"
    
    if [[ -n "$syzygy_path" ]]; then
        echo -e "${BLUE}  python3 src/main.py --syzygy-path '$syzygy_path'${NC}"
    fi
    
    echo
    echo "For more options: python3 src/main.py --help"
    
    # Test the installation
    echo
    if get_yes_no "Test the installation now?" "y"; then
        echo -e "${YELLOW}Testing installation...${NC}"
        if python3 -c "
import sys
sys.path.append('src')
try:
    from engine_handler import get_engine
    engine = get_engine('$stockfish_path')
    engine.quit()
    print('✓ Engine test successful!')
except Exception as e:
    print(f'✗ Engine test failed: {e}')
    sys.exit(1)
"; then
            echo -e "${GREEN}Installation test passed!${NC}"
        else
            echo -e "${RED}Installation test failed. Please check the configuration.${NC}"
        fi
    fi
}

# Run main function
main "$@"