#!/usr/bin/env bash
# ==============================================================================
# TPCMS - Training, Programme & Certificate Management System Launcher
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================================"
echo "  🚀 TRAINING, PROGRAMME & CERTIFICATE MANAGEMENT SYSTEM (TPCMS)"
echo "======================================================================"

# Determine Python runtime
if [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="./venv/bin/python3"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python not found. Please install Python 3.9+."
    exit 1
fi

echo "🔍 Using Python: $($PYTHON_CMD --version)"
echo "📡 Starting server on http://localhost:5050 ..."
echo "----------------------------------------------------------------------"
echo "  • UI Dashboard:              http://localhost:5050"
echo "  • Public Verification:       http://localhost:5050/#verify"
echo "  • MySQL Console:             http://localhost:5050 (Click MySQL Console)"
echo "======================================================================"

exec $PYTHON_CMD app.py
