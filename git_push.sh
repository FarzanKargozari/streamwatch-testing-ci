
#!/bin/bash
set -e

# Stage only the intended files
git add network_client.py test_network_client.py

# Check for whitespace errors
git diff --cached --check

# Stop if there are no staged changes
if git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

# Show the files being committed
git diff --cached --stat

# Commit with a descriptive message
git commit -m "${1:-Update network tests}"

# Push to GitHub
git push origin main

echo "Successfully pushed to GitHub!"
