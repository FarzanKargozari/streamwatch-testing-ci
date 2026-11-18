
#!/bin/bash
set -e

# Prevent committing unrelated staged changes
if ! git diff --cached --quiet; then
    echo "ERROR: Some files are already staged."
    echo "Review them before running this script."
    git diff --cached --name-only
    exit 1
fi


# Require a commit message and at least one file
if [ "$#" -lt 2 ]; then
    echo "Usage: bash git_push.sh 'Commit message' file1 [file2 ...]"
    exit 1
fi

message="$1"
shift

# Run automated tests before committing
echo "Running automated tests..."
bash run_tests.sh

# Stage only the requested files
git add -- "$@"

# Check staged changes
git diff --cached --check

if git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

echo "Files staged for commit:"
git diff --cached --stat

# Require confirmation before publishing
read -r -p "Commit and push these changes? (yes/no): " answer

if [ "$answer" != "yes" ]; then
    echo "Cancelled. No commit or push performed."
    exit 0
fi

git commit -m "$message"
git push origin main

echo "Successfully pushed to GitHub!"
