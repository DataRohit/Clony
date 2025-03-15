#!/bin/bash

# Activate virtual environment
source .venv/Scripts/activate

# Print header
echo "========================================"
echo "Running Ruff checks and fixes"
echo "========================================"

# Run Ruff checks
python -m ruff check .

# Check if there were any issues
if [ $? -ne 0 ]; then
    echo "Ruff found issues. Attempting to fix..."
    python -m ruff check --fix .
    
    # Check if fixes were successful
    if [ $? -ne 0 ]; then
        echo "Some issues could not be automatically fixed. Please fix them manually."
    else
        echo "Ruff fixes applied successfully."
    fi
else
    echo "No Ruff issues found."
fi

echo ""
echo "========================================"
echo "Running pytest"
echo "========================================"

# Run pytest with coverage
python -m pytest

# Print completion message
echo ""
echo "========================================"
echo "Check and test process completed"
echo "========================================" 