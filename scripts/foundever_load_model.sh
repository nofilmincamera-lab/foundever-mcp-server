#!/bin/bash
# Foundever Model Loader
# Automatically loads the Foundever voice model into Ollama
# Can be called by MCP server or run manually

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="/media/willard/New Volume/foundever_model_quantized"
MODEL_NAME="${1:-foundever-voice-q5}"
MODEL_FILE="foundever-voice-q5_k_m.gguf"

echo "==============================================="
echo "Foundever Voice Model Loader"
echo "==============================================="
echo ""

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Check if model already exists
if ollama list | grep -q "$MODEL_NAME"; then
    echo "✓ Model '$MODEL_NAME' already loaded in Ollama"
    echo ""
    echo "Available models:"
    ollama list | grep foundever
    exit 0
fi

echo "📦 Loading Foundever Voice model into Ollama..."
echo "   Model: $MODEL_FILE"
echo "   Name: $MODEL_NAME"
echo ""

# Create Modelfile
MODELFILE="$MODEL_DIR/Modelfile"
cat > "$MODELFILE" <<'EOF'
FROM /media/willard/New Volume/foundever_model_quantized/foundever-voice-q5_k_m.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>
"""

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"

SYSTEM """You are a Foundever RFP response assistant. You write in Foundever's professional voice, using specific patterns:
- Confirmation syntax for acknowledging requirements
- Value bridges connecting features to client benefits
- So-what closes summarizing value propositions
Always use {{placeholders}} for specific client data you don't have."""
EOF

echo "✓ Modelfile created"

# Load into Ollama
echo "⏳ Creating Ollama model (this may take 30-60 seconds)..."
if ollama create "$MODEL_NAME:latest" -f "$MODELFILE"; then
    echo ""
    echo "✅ SUCCESS! Model loaded as '$MODEL_NAME:latest'"
    echo ""
    echo "Available Foundever models:"
    ollama list | grep foundever
    echo ""
    echo "Usage:"
    echo "  ollama run $MODEL_NAME:latest"
else
    echo ""
    echo "❌ Failed to load model"
    exit 1
fi

echo ""
echo "==============================================="
