#!/bin/bash
set -e
set -o pipefail
cd $(dirname "$0")

python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 --version 1.0.0 \
    -- python ./server.py --name s2 --version 2.0.0
