# Foundever MCP Utilities

This directory contains utility scripts and tools for working with Foundever MCP.

## Available Utilities

### foundever_voice_reviewer.py

**Purpose:** Analyze slides and documents using the Foundever Voice model to assess alignment with Foundever's writing standards.

**Features:**
- Semantic analysis of slide content
- Voice alignment scoring (1-10)
- Detection of Foundever voice patterns:
  - Confirmation syntax
  - Value bridges
  - So-what closes
- Rankings of best/worst aligned content
- Detailed improvement suggestions

**Usage:**
```bash
cd /home/willard/foundever-mcp-server/utils
python3 foundever_voice_reviewer.py
```

**Requirements:**
- Ollama running with foundever-voice-q5:latest model
- httpx Python package
- Slide text files in target directory

**Output:**
- JSON file with detailed analysis
- Console summary of findings
- Rankings by voice alignment

## Adding New Utilities

To add a new utility:
1. Create a Python script in this directory
2. Follow the naming convention: `foundever_<purpose>.py`
3. Include docstring documentation
4. Update this README with usage instructions
