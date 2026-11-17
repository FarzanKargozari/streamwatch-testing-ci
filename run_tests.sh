
#!/bin/bash

echo "Starting StreamWatch automated tests..."

.venv/bin/python -m pytest -v --junitxml=test-results.xml --cov=streamwatch --cov-branch --cov-report=term-missing --cov-report=xml:coverage.xml
if [ $? -eq 0 ]; then
    echo "SUCCESS: All tests passed!"
else
    echo "FAILED: Some tests failed!"
    exit 1
fi
# Jenkins automatic GitHub polling test
