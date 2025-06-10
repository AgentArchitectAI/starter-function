# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a professional Python-based Appwrite function for generating DXF files (AutoCAD drawing format) from JSON instructions. The system converts structured JSON data into industry-standard DXF format using the `ezdxf` library with comprehensive validation, error handling, and processing summaries.

## Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Run single test**: `python3 test_step1.py` (or any test_step*.py file)
- **Run comprehensive tests**: `python3 test_comprehensive.py` (requires pytest: `pip install pytest`)
- **Run all step tests**: `python3 test_step1.py && python3 test_step2.py && python3 test_step3.py && python3 test_step4.py && python3 test_step5_simple.py`
- **Entrypoint**: `src/main.py`
- **Runtime**: Python 3.9

## Architecture Overview

The system uses a modern object-oriented architecture with these key design patterns:

### Factory Pattern
- `EntityFactory`: Creates appropriate processors for 19 different entity types
- `EntityProcessor` abstract base class with concrete implementations for each entity type

### Request Processing Pipeline
- `RequestValidator`: Middleware for size limits and layer validation
- `DXFRequestModel`: Pydantic-based JSON schema validation
- `GeometryValidator`: Geometric parameter validation

### Core Classes
- `DXFGenerator`: Main orchestration class for DXF generation workflow
- `ProcessingSummary`: Detailed reporting with metrics and timing
- `TempFileManager`: Professional file lifecycle management with automatic cleanup
- `CoordinateConverter`: Safe coordinate conversion utilities

### Supported Entity Categories (19 types)
- **Basic Geometry**: rectangle, circle, line, text, arc
- **Advanced Geometry**: spline, polyline, ellipse, solid, mesh  
- **Annotations**: dimension, leader, hatch, mtext
- **Professional Features**: viewport, linetype, layer_state, attribute
- **Coordinate Systems**: coordinate_system (UCS, transforms)

## API Endpoints

- **GET /ping**: Health check returning "Pong"
- **POST /**: Main DXF generation endpoint with comprehensive features:
  - Binary DXF file response or JSON processing summary
  - Streaming support for large files (>1MB)
  - Request validation with size limits (max 10,000 entities)
  - Detailed processing summaries in response headers

## Configuration & Validation

- **Timeout**: 15 seconds
- **Environment**: No environment variables required  
- **File Management**: Professional temporary file handling in `/tmp` with automatic cleanup
- **Request Limits**: Max 10,000 entities, max 50,000 mesh vertices
- **Validation**: Comprehensive Pydantic models with geometric parameter validation
- **Error Handling**: Graceful degradation with detailed error reporting and logging

## Testing

The codebase includes comprehensive testing across 5 validation steps:
- `test_step1.py`: Foundation validation (Pydantic, logging, type safety)
- `test_step2.py`: Architecture and error handling
- `test_step3.py`: Professional entity system (19 entity types)
- `test_step4.py`: API improvements and streaming
- `test_step5_simple.py`: Integration tests and kitchen layout examples
- `test_comprehensive.py`: Full pytest test suite with mock testing