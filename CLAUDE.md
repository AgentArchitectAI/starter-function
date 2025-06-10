# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Appwrite function for generating DXF files (AutoCAD drawing format) from JSON instructions. The main functionality converts structured JSON data containing layers, blocks, and geometric figures into DXF format using the `ezdxf` library.

## Commands

- **Install dependencies**: `pip install -r requirements.txt`
- **Entrypoint**: `src/main.py`
- **Runtime**: Python 3.9

## Function Architecture

The function accepts POST requests with JSON data containing:
- `capas` (layers): Layer definitions with names and colors
- `bloques` (blocks): Reusable block definitions with entities
- `figuras` (figures): Main drawing entities (rectangles, circles, lines, text, arcs, ellipses, hatches, dimensions, 3D polylines)

Key components:
- `generar_dxf_desde_instrucciones()`: Core DXF generation function
- `safe_tuple_float()`: Utility for safe coordinate conversion
- Error handling with detailed logging throughout

## API Endpoints

- **GET /ping**: Health check returning "Pong"
- **POST /**: Main endpoint for DXF generation, returns binary DXF file

## Configuration

- Timeout: 15 seconds
- No environment variables required
- Files generated in `/tmp` directory with random UUID filenames