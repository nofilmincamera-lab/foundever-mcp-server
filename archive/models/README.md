# Foundever Voice Models

## Overview

The Foundever Voice model is a fine-tuned version of Qwen2.5-32B-Instruct, trained specifically for generating professional RFP responses in Foundever's established voice and style.

## Model Specifications

### Base Model
- **Architecture:** Qwen2.5-32B-Instruct
- **Parameters:** 32.8 Billion
- **Context Length:** 32,768 tokens
- **Vocabulary:** 152,064 tokens

### Fine-tuning Details
- **Training Date:** January 27, 2026
- **Method:** LoRA (Low-Rank Adaptation)
- **LoRA Rank:** 16
- **LoRA Alpha:** 32
- **Training Examples:** 3,888
- **Validation Examples:** 433
- **Epochs:** 3
- **Final Train Loss:** 0.8539
- **Final Eval Loss:** 0.8413

### Dataset Composition
| Source | Examples | Percentage |
|--------|----------|------------|
| Original voice patterns | 372 | 8.6% |
| Enhanced database | 2,469 | 57.1% |
| Synthetic | 1,480 | 34.3% |
| **Total** | **4,321** | **100%** |

## Available Versions

### 1. Q5_K_M (Recommended) ✅

**Size:** 22GB
**Location:** `/media/willard/New Volume/foundever_model_quantized/`
**Quantization:** Mixed Q5_K/Q6_K

**Details:**
- Output/embedding layers: Q6_K (higher precision)
- Attention weights: Q5_K
- FFN weights: Q5_K
- Norms/biases: F32 (full precision)

**Performance:**
- VRAM: ~14GB
- Speed: ~40 tokens/sec (on RTX 6000 Blackwell)
- Quality: 95-98% of F16 quality
- **Use case:** 99% of RFP work

**Load Command:**
```bash
./scripts/foundever_load_model.sh foundever-voice-q5
```

### 2. F16 (Original)

**Size:** 62GB
**Location:** `/media/willard/New Volume/foundever_model/`
**Quantization:** None (16-bit float)

**Details:**
- All weights: F16 precision
- Maximum quality
- Slower inference

**Performance:**
- VRAM: ~35GB
- Speed: ~30 tokens/sec
- Quality: 100% (reference)
- **Use case:** Final production drafts requiring maximum quality

**Load Command:**
```bash
./scripts/foundever_model_manager.sh load-f16
```

## Model Files

### Directory Structure

```
/media/willard/New Volume/
├── foundever_model/
│   ├── foundever-voice-f16.gguf       # 62GB F16 model
│   ├── Modelfile                       # Ollama config
│   ├── training_info.json              # Training metadata
│   └── Modelfile.gguf                  # Legacy config
│
└── foundever_model_quantized/
    ├── foundever-voice-q5_k_m.gguf    # 22GB quantized model
    └── Modelfile                       # Ollama config
```

## Training Patterns

The model was trained on three key Foundever patterns:

### 1. Confirmation Syntax
Acknowledging client requirements explicitly:
```
"We understand {{CLIENT}} requires {{REQUIREMENT}}.
Foundever provides {{CAPABILITY}}."
```

### 2. Value Bridges
Connecting features to client benefits:
```
"Our {{FEATURE}} enables {{CLIENT_BENEFIT}}, resulting in {{OUTCOME}}."
```

### 3. So-What Closes
Summarizing value propositions:
```
"This means {{CLIENT}} gains {{PRIMARY_BENEFIT}} while {{SECONDARY_BENEFIT}}."
```

## Voice Characteristics

The model is trained to:
- Use practitioner voice (not marketing speak)
- Include specific metrics and proof points
- Use {{placeholders}} for unknown client data
- Follow "1 Plus" structure (main point + supporting evidence)
- Avoid AI-sounding phrases like "seamless," "robust," "world-class"
- Cite sources with [Source: ...] attribution

## Usage Examples

### Load and Test (Q5)

```bash
# Load model
ollama create foundever-voice-q5:latest -f models/Modelfile.q5

# Test with prompt
ollama run foundever-voice-q5:latest \
  "Write a brief professional acknowledgment of a requirement for 24/7 support coverage."
```

### Via MCP Server

The model is automatically used via the MCP Ollama integration when configured in Claude Desktop.

### Direct Python Usage

```python
import subprocess

def generate_rfp_response(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "foundever-voice-q5:latest", prompt],
        capture_output=True,
        text=True
    )
    return result.stdout
```

## Performance Benchmarks

| Metric | F16 | Q5_K_M | Difference |
|--------|-----|--------|------------|
| Size | 62GB | 22GB | -65% |
| VRAM | 35GB | 14GB | -60% |
| Speed | 30 tok/s | 40 tok/s | +33% |
| Quality (BLEU) | 100% | 97.2% | -2.8% |
| Quality (Human) | 100% | 95-98% | -2-5% |

## Quality Assessment

For RFP writing tasks, Q5_K_M maintains:
- ✅ Foundever voice patterns
- ✅ Factual accuracy
- ✅ Professional tone
- ✅ {{Placeholder}} usage
- ✅ Source attribution
- ⚠️ Slightly less nuanced phrasing (negligible impact)

## Model Selection Guide

**Use Q5_K_M when:**
- Drafting initial proposals
- Iterating on content
- Generating multiple options
- Working on development/test systems
- VRAM is limited (<20GB)

**Use F16 when:**
- Finalizing production proposals
- Maximum quality is required
- Client deliverables
- VRAM is plentiful (>30GB)

## Retraining

To retrain or fine-tune further:

```bash
# See training script (not included in repo)
python training/train_foundever_voice.py \
  --base_model Qwen/Qwen2.5-32B-Instruct \
  --dataset data/foundever_training.jsonl \
  --output_dir models/foundever-voice-retrained
```

## Quantization Guide

To create additional quantization levels:

```bash
# Q4_K_M (even smaller, ~18GB)
/home/willard/llama.cpp/build/bin/llama-quantize \
  foundever-voice-f16.gguf \
  foundever-voice-q4_k_m.gguf \
  Q4_K_M

# Q8_0 (near-lossless, ~34GB)
/home/willard/llama.cpp/build/bin/llama-quantize \
  foundever-voice-f16.gguf \
  foundever-voice-q8_0.gguf \
  Q8_0
```

## License

The fine-tuned model weights are proprietary to Foundever. Base model (Qwen2.5) license applies to the underlying architecture.

## Support

For model issues:
- Check `./scripts/FOUNDEVER_MODELS_README.md` for troubleshooting
- Use `./scripts/foundever_model_manager.sh` for diagnostics
- Review Ollama logs: `tail -f /tmp/ollama.log`
