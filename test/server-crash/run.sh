#!/bin/bash
cd $(dirname "$0")

# Server s2 will crash after initialization
# We expect rass to exit with error code 1

# On Windows rass can't make its fatal exit while the stdin-reading
# executor thread is blocked (see the FIXME in test2.py), so this
# scenario isn't testable there
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || -n "$WINDIR" ]]; then
    echo "Windows, skipping test" >&2
    exit 77
fi

set +e
python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 \
    -- python ./server.py --name s2 --crash-after-init
EXIT_CODE=$?
set -e

# Check if rass exited with error (expected behavior)
if [ $EXIT_CODE -eq 1 ]; then
    exit 0  # Test passed - rass exited with error as expected
else
    echo "Test failed: Expected exit code 1, got $EXIT_CODE"
    exit 1
fi
