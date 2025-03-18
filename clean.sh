#!/bin/bash
rm -rf build/
rm -rf dist/
rm -rf src/*.egg-info/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true