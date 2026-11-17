
#!/bin/bash

echo "Starting StreamWatch automated tests..."

python -m pytest -v

if [ $? -eq 0 ]; then
    echo "SUCCESS: All tests passed!"
else
    echo "FAILED: Some tests failed!"
    exit 1
fi
