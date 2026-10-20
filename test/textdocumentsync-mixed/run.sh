#!/bin/bash
set -e
cd $(dirname "$0")

# s1 (primary) is incremental, s2 (secondary) is full: rass must
# advertise Incremental and translate didChange for the full server
# (#55).  The third one poses as ruby-lsp, which rejects range-less
# changes, so rass must reopen the document instead.
python ../yoyo.py ./client.py --rass-- \
    -- python ./server.py --name s1 --text-document-sync 2 \
    -- python ./server.py --name s2 --text-document-sync 1 \
    -- python ./server.py --name 'Ruby LSP' --text-document-sync 2
