#!/bin/bash
# Foundever Model Manager
# Homepage script for managing Foundever voice models
# Provides options for both F16 (62GB) and Q5_K_M (22GB) versions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR_F16="/media/willard/New Volume/foundever_model"
MODEL_DIR_Q5="/media/willard/New Volume/foundever_model_quantized"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo -e "${BLUE}     Foundever Voice Model Manager${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
    echo ""

    # Check Ollama status
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama: Running"
    else
        echo -e "${RED}✗${NC} Ollama: Not running"
    fi

    # Check models
    echo ""
    echo "Available Models:"
    echo ""

    # F16 Model
    if [ -f "$MODEL_DIR_F16/foundever-voice-f16.gguf" ]; then
        SIZE=$(du -sh "$MODEL_DIR_F16/foundever-voice-f16.gguf" | cut -f1)
        echo -e "  ${GREEN}✓${NC} F16 (High Quality):  $SIZE - $MODEL_DIR_F16/"
    else
        echo -e "  ${RED}✗${NC} F16 model not found"
    fi

    # Q5_K_M Model
    if [ -f "$MODEL_DIR_Q5/foundever-voice-q5_k_m.gguf" ]; then
        SIZE=$(du -sh "$MODEL_DIR_Q5/foundever-voice-q5_k_m.gguf" | cut -f1)
        echo -e "  ${GREEN}✓${NC} Q5_K_M (Optimized): $SIZE - $MODEL_DIR_Q5/"
    else
        echo -e "  ${RED}✗${NC} Q5_K_M model not found"
    fi

    echo ""
    echo "Loaded in Ollama:"
    if ollama list 2>/dev/null | grep -q "foundever"; then
        ollama list | grep foundever | while read line; do
            echo -e "  ${GREEN}✓${NC} $line"
        done
    else
        echo -e "  ${YELLOW}⚠${NC}  No Foundever models loaded"
    fi
    echo ""
}

load_f16() {
    echo ""
    echo -e "${YELLOW}Loading F16 model (62GB, highest quality)...${NC}"

    MODELFILE="$MODEL_DIR_F16/Modelfile"
    ollama create foundever-voice-f16:latest -f "$MODELFILE"

    echo -e "${GREEN}✓ F16 model loaded as 'foundever-voice-f16:latest'${NC}"
}

load_q5() {
    echo ""
    echo -e "${YELLOW}Loading Q5_K_M model (22GB, recommended)...${NC}"

    # Use the dedicated loader script
    "$SCRIPT_DIR/foundever_load_model.sh" foundever-voice-q5
}

test_model() {
    MODEL_NAME="$1"

    echo ""
    echo -e "${YELLOW}Testing $MODEL_NAME...${NC}"
    echo ""

    TEST_PROMPT="Write a brief professional acknowledgment of a client requirement for 24/7 support coverage."

    echo "Prompt: $TEST_PROMPT"
    echo ""
    echo "Response:"
    echo "---"

    ollama run "$MODEL_NAME:latest" "$TEST_PROMPT"

    echo "---"
    echo ""
}

unload_model() {
    MODEL_NAME="$1"
    echo ""
    echo -e "${YELLOW}Removing $MODEL_NAME from Ollama...${NC}"
    ollama rm "$MODEL_NAME:latest"
    echo -e "${GREEN}✓ Model removed${NC}"
}

show_menu() {
    show_status

    echo "Actions:"
    echo "  1) Load F16 model (62GB, highest quality)"
    echo "  2) Load Q5_K_M model (22GB, recommended)"
    echo "  3) Test F16 model"
    echo "  4) Test Q5_K_M model"
    echo "  5) Unload F16 model"
    echo "  6) Unload Q5_K_M model"
    echo "  7) Start Ollama server"
    echo "  8) Refresh status"
    echo "  q) Quit"
    echo ""
    echo -n "Choice: "
}

# Main menu loop
if [ "$1" == "status" ]; then
    show_status
    exit 0
fi

if [ "$1" == "load-f16" ]; then
    load_f16
    exit 0
fi

if [ "$1" == "load-q5" ]; then
    load_q5
    exit 0
fi

while true; do
    show_menu
    read -r choice

    case $choice in
        1) load_f16 ;;
        2) load_q5 ;;
        3) test_model "foundever-voice-f16" ;;
        4) test_model "foundever-voice-q5" ;;
        5) unload_model "foundever-voice-f16" ;;
        6) unload_model "foundever-voice-q5" ;;
        7)
            echo "Starting Ollama..."
            ollama serve &
            sleep 2
            ;;
        8) clear ;;
        q|Q)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            sleep 1
            ;;
    esac
done
