# Archive Directory

This directory contains files that are not directly served by the MCP server but are valuable for development, testing, and documentation.

## Contents

### docs/
Complete documentation suite including:
- `DOCUMENTATION.md` - Comprehensive technical documentation
- `README.md` - Original documentation
- `archive/` - Historical documents and reports
  - GitHub creation reports
  - Repository summaries
  - AI competency evaluations
  - Competitive content skills

### utils/
Utility scripts and tools:
- `foundever_voice_reviewer.py` - Slide analysis tool using Foundever Voice model
- Various helper scripts for development

### tests/
Test suite (placeholder for future tests):
- Unit tests for MCP server
- Integration tests for enrichment engine
- Search and embedding tests

### models/
Model documentation:
- `README.md` - Complete model specifications
- Training data information
- Benchmark results
- Model file locations

### QUICKSTART.md
Quick setup guide for new users (5-minute installation).

## Why Archive These Files?

The MCP server directly serves only:
- `src/` - Core Python modules
- `scripts/` - Model management scripts
- `config/` - Configuration files
- `prompts/` - System prompts
- `requirements.txt` - Dependencies
- `README.md` - Main documentation
- `LICENSE` - MIT license

All other files are supporting materials that don't need to be in the root directory. By archiving them:
1. **Cleaner Structure** - Root directory shows only what MCP serves
2. **Easier Navigation** - New contributors see core files immediately
3. **Better Organization** - Related materials grouped together
4. **Preserved History** - Nothing is deleted, just organized

## Accessing Archived Files

All files remain in the repository and can be accessed:
```bash
cd /home/willard/foundever-mcp-server/archive

# View documentation
cat docs/DOCUMENTATION.md

# Run utilities
python3 utils/foundever_voice_reviewer.py

# Read model specs
cat models/README.md
```

## When to Use Archive vs Root

**Keep in Root:**
- Files that MCP server imports or executes
- Core configuration that changes how MCP runs
- Essential documentation (README, LICENSE)

**Move to Archive:**
- Development tools and utilities
- Extended documentation and guides
- Test files (when not actively running)
- Historical reports and analyses
- Reference materials

## Related Documentation

- [Main README](../README.md) - MCP server overview
- [Complete Docs](docs/DOCUMENTATION.md) - Technical reference
- [Prompts](../prompts/README.md) - System prompts documentation
