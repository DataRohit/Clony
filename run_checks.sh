#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Print header
echo "========================================"
echo "Running Ruff checks and fixes"
echo "========================================"

# Run Ruff checks
echo "Running initial Ruff checks..."
if python -m ruff check .; then
    echo "✓ No Ruff issues found."
else
    echo "Ruff found issues. Attempting to fix..."
    if python -m ruff check --fix .; then
        echo "✓ Ruff fixes applied successfully."
    else
        echo "⚠ Some issues could not be automatically fixed. Please fix them manually."
    fi
fi

echo ""
echo "========================================"
echo "Running pytest with coverage"
echo "========================================"

# Run pytest with coverage
echo "Running tests with coverage report..."
python -m pytest --cov=. --cov-report=term-missing

# Check if tests passed
TEST_EXIT_CODE=$?
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed successfully."
else
    echo "⚠ Some tests failed. Please review the test output."
fi

# Print completion message
echo ""
echo "========================================"
echo "Check and test process completed"
echo "========================================"

# Check if any files were modified during the process
if git diff --quiet; then
    echo "No files were modified during checks."
else
    echo "The following files were modified:"
    git diff --name-only
fi

# Exit with the pytest exit code
exit $TEST_EXIT_CODE