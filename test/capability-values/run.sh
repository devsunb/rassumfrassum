#!/bin/bash
set -e
cd $(dirname "$0")

# s1 advertises codeActionProvider and completionProvider as {} and
# definitionProvider as false
# s2 advertises codeActionProvider and definitionProvider as true
# Expected: codeAction goes to s1 and s2, completion only to s1,
# definition only to s2
python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 \
       --code-action '{}' --definition false --completion '{}' \
    -- python ./server.py --name s2 \
       --code-action true --definition true

# s1 advertises completionProvider as {} and s2 as true: a triggered
# completion still gets an answer
python ../yoyo.py ./client.py --trigger --rass-- \
    -- python ./server.py --name s1 \
       --code-action true --definition true --completion '{}' \
    -- python ./server.py --name s2 \
       --code-action true --definition true --completion true
