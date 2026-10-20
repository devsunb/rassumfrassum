#!/bin/bash
set -e
cd $(dirname "$0")

# S1 (primary) responds immediately
# S2 (secondary) delays initialize response by 4000ms, beyond the usual
# 3000ms aggregation timeout but within the initialize timeout, and is
# the only definition provider

python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 \
    -- python ./server.py --name s2 --initialize-delay 4000 --definition
