# Foundever Voice Model Setup

## Models Available

### 1. F16 (Original) - 62GB
**Location:** `/media/willard/New Volume/foundever_model/`
- **Quality:** Highest (16-bit float)
- **Size:** 62GB
- **Use when:** Maximum quality is required, plenty of VRAM available

### 2. Q5_K_M (Quantized) - 22GB ✅ RECOMMENDED
**Location:** `/media/willard/New Volume/foundever_model_quantized/`
- **Quality:** Very Good (mixed quantization)
- **Size:** 22GB (saves 40GB!)
- **Use when:** Balanced quality/performance is needed (most cases)

**Training Info:**
- Base: Qwen/Qwen2.5-32B-Instruct
- Training: 3,888 examples, 3 epochs
- Trained: 2026-01-27
- Purpose: Foundever RFP professional voice

## Scripts

### 🏠 Homepage Manager (Interactive)
```bash
~/foundever_model_manager.sh
```
**Features:**
- Status dashboard showing both models
- Load/unload models from Ollama
- Test models with sample prompts
- Manage Ollama server

**Quick commands:**
```bash
# Just show status
~/foundever_model_manager.sh status

# Load Q5 model directly
~/foundever_model_manager.sh load-q5

# Load F16 model directly
~/foundever_model_manager.sh load-f16
```

### 🤖 MCP Auto-Loader
```bash
~/foundever_load_model.sh [model-name]
```
**Purpose:** Can be called by MCP server to auto-load model on demand

**Usage:**
```bash
# Load Q5 model (default)
~/foundever_load_model.sh foundever-voice-q5

# Load with custom name
~/foundever_load_model.sh my-custom-name
```

## Using with Ollama

### Load Manually (Q5 - Recommended)
```bash
# Create Modelfile
cat > /tmp/foundever_q5.Modelfile <<'EOF'
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

SYSTEM """You are a Foundever RFP response assistant. You write in Foundever's professional voice."""
EOF

# Load into Ollama
ollama create foundever-voice-q5:latest -f /tmp/foundever_q5.Modelfile

# Test it
ollama run foundever-voice-q5:latest "Write a brief acknowledgment of 24/7 support coverage."
```

### Load Manually (F16 - High Quality)
```bash
# Use existing Modelfile
ollama create foundever-voice-f16:latest -f "/media/willard/New Volume/foundever_model/Modelfile"
```

## MCP Integration

The model can be auto-loaded by the MCP server when needed.

### Update MCP Config
Edit `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "npx",
      "args": ["-y", "mcp-ollama"],
      "env": {
        "OLLAMA_HOST": "http://localhost:11434",
        "OLLAMA_MODEL": "foundever-voice-q5:latest"
      }
    }
  }
}
```

### MCP Auto-Load Hook
You can configure the MCP server to automatically load the model when it's not available:

```python
# In your MCP server code
import subprocess

def ensure_foundever_model():
    result = subprocess.run(
        ["/home/willard/foundever_load_model.sh", "foundever-voice-q5"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Failed to load model: {result.stderr}")
```

## Quantization Details

The Q5_K_M quantization uses:
- **Q6_K** for output/embedding layers (higher precision)
- **Q5_K** for attention/FFN weights (good balance)
- **F32** for norms/biases (full precision)

**Quality Impact:** Minimal for RFP writing tasks. The mixed quantization preserves coherence and factual accuracy while reducing size by 65%.

## Troubleshooting

### Ollama Permission Issues
If you see "permission denied" errors:

```bash
# Check Ollama data location
ls -la ~/.ollama

# If it's a symlink to a restricted location, temporarily use local storage
unlink ~/.ollama
mkdir ~/.ollama
ollama create foundever-voice-q5:latest -f /tmp/foundever_q5.Modelfile
```

### Model Not Loading
```bash
# Check Ollama is running
pgrep ollama

# Start if needed
ollama serve &

# Check logs
tail -f /tmp/ollama.log
```

### Out of VRAM
Use Q5 model (22GB) instead of F16 (62GB). If still out of memory, consider:
- Using Q4_K_M quantization (saves another ~4GB)
- Offloading fewer layers to GPU
- Running on CPU with slower inference

## Model Comparison

| Aspect | F16 (62GB) | Q5_K_M (22GB) |
|--------|------------|---------------|
| Quality | Best | Very Good |
| VRAM | ~35GB+ | ~14GB |
| Speed | Slower (more data) | Faster |
| Use Case | Final production drafts | Development & iteration |

For most RFP work, **Q5_K_M is recommended** - the quality difference is negligible for professional writing tasks.
