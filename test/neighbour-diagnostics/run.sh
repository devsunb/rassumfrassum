#!/bin/bash
set -e
cd $(dirname "$0")

python ../yoyo.py ./client.py --rass-- --stream-diagnostics \
    -- python ./server.py --name s1 --inter-file \
    -- python ./server.py --name s2
