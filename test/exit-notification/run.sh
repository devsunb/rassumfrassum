#!/bin/bash
set -e
cd $(dirname "$0")

servers=(-- python ./server.py --name s1 --exit-marker s1.exited
         -- python ./server.py --name s2 --exit-marker s2.exited)

# The servers write s1.exited and s2.exited when they get 'exit'
rm -f s1.exited s2.exited
python ../yoyo.py ./client.py --rass-- "${servers[@]}"

# 'exit' without 'shutdown' first: rass exits with 1, as servers must
rm -f s1.exited s2.exited
rc=0
python ../yoyo.py ./client.py --no-shutdown --rass-- "${servers[@]}" || rc=$?
[ "$rc" -eq 1 ]
