# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Manta is a Python wrapper for the dotabuff/manta Go library that parses Dota 2 replay files (.dem). It uses CGO to create Python bindings for the Go parser, implementing all 272 Manta callbacks for comprehensive replay data extraction.

## Architecture

The library consists of three main layers:

1. **Go CGO Layer** (`go_wrapper/`): Contains the Go code that wraps the Manta parser library
   - `manta_wrapper.go`: Main CGO export functions
   - `universal_parser.go`: Universal message parsing implementation
   - `callbacks_*.go`: Implementation of all 272 Manta callbacks organized by category

2. **Python Bindings** (`src/python_manta/`): Python ctypes interface to the Go shared library
   - `manta_python.py`: Main parser class and ctypes configuration
   - Uses Pydantic models for type safety and validation

3. **Shared Library** (`libmanta_wrapper.so`): Built CGO library that bridges Go and Python

The data flow is: Python → ctypes → CGO → Go Manta parser → JSON → Python Pydantic models

## Essential Commands

### Build the library
```bash
./build.sh
```
This script:
- Checks for Go and Python prerequisites
- Verifies the Manta repository exists at `../manta`
- Builds the CGO shared library
- Copies it to the Python package directory
- Verifies the Python import works

### Run tests
```bash
# Run unit tests only (fast, no demo files needed)
python run_tests.py --unit

# Run integration tests (requires demo files)
python run_tests.py --integration  

# Run with coverage analysis
python run_tests.py --coverage

# Run specific test file
python run_tests.py tests/test_models.py

# Run all tests
python run_tests.py --all
```

### Install in development mode
```bash
# Install with dev dependencies (includes pytest, pytest-cov, etc.)
pip install -e '.[dev]'

# OR with uv (faster)
uv pip install -e '.[dev]'

# OR just the package without dev tools
pip install -e .
```

### Quick validation
```bash
# Test the library works (update demo path in file first)
python simple_example.py
```

## Testing Strategy

The project uses pytest with the following test categories:
- **Unit tests** (`-m unit`): Test models and pure Python code without external dependencies
- **Integration tests** (`-m integration`): Test the full parsing pipeline with real demo files
- **Performance tests** (`-m slow`): Test parsing performance with large files

Coverage requirement is 90% as configured in `pytest.ini`.

## Key Implementation Details

1. **Memory Management**: The Go code allocates C strings that must be freed. The Python code handles this via the `FreeString` export.

2. **Message Filtering**: The universal parser supports filtering by message type name (e.g., "CDOTAUserMsg_ChatMessage") and limits the number of messages to prevent memory issues.

3. **JSON Serialization**: All data exchange between Go and Python happens via JSON strings to avoid complex struct marshaling.

4. **Callback Registration**: The Go wrapper dynamically registers callbacks based on the filter parameter, supporting all 272 Manta message types.

## Dependencies

**Build Requirements**:
- Go 1.19+ 
- Python 3.8+
- Manta repository cloned at `../manta`

**Python Dependencies**:
- pydantic>=2.0.0 (required)
- pytest, pytest-cov (for testing)

## Common Development Tasks

### Adding a new message type parser
1. Check if the callback already exists in `callbacks_*.go` files
2. If not, add it to the appropriate callbacks file
3. The universal parser will automatically support it

### Debugging parsing issues
1. Check the demo file exists and is readable
2. Verify the message type name matches exactly (case-sensitive)
3. Use smaller `max_messages` values to isolate issues
4. Check the Go build output for any CGO warnings