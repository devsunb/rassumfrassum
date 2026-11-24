#!/bin/bash
set -e
cd $(dirname "$0")

python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 \
    -- python ./server.py --name s2
