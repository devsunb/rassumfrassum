#!/usr/bin/env python
"""
Server that, like real ones, keeps running after 'shutdown' and only
exits cleanly on 'exit', which it records in a marker file.
"""

import argparse
import sys
from pathlib import Path

from rassumfrassum.json import read_message_sync, write_message_sync

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--exit-marker', required=True)
args = parser.parse_args()

while (msg := read_message_sync()) is not None:
    method = msg.get('method')
    msg_id = msg.get('id')
    if method == 'exit':
        Path(args.exit_marker).write_text(args.name)
        sys.exit(0)
    elif method == 'initialize':
        write_message_sync({
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': {'capabilities': {}, 'serverInfo': {'name': args.name}}
        })
    elif msg_id is not None and method:
        write_message_sync({'jsonrpc': '2.0', 'id': msg_id, 'result': None})

# EOF without 'exit'
sys.exit(1)
