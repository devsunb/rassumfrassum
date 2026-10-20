#!/bin/bash
set -e
cd $(dirname "$0")

# S1 (primary) responds immediately
# S2 (secondary) delays initialize response by 3000ms (exceeds the
# 2500ms timeout set here)

python ../yoyo.py ./client.py --rass-- --drop-tardy --initialize-timeout-ms 2500 \
    -- python ./server.py --name s1 \
    -- python ./server.py --name s2 --initialize-delay 3000
