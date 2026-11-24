#!/usr/bin/env python
"""
Server for the dynamic-registration test.  s1 sends the client whatever
server request the client asks for in a 'test/send' request.
"""

import argparse

from rassumfrassum.json import write_message_sync
from rassumfrassum.test2 import run_toy_server

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
args = parser.parse_args()

sent = 0

def handle_send(_msg_id, params):
    global sent
    sent += 1
    write_message_sync({
        'jsonrpc': '2.0',
        'id': f'{args.name}-{sent}',
        'method': params['method'],
        'params': params['params'],
    })

def answer(_msg_id, _params):
    return [{'title': f'from {args.name}'}]

def complete(_msg_id, _params):
    return {'isIncomplete': False, 'items': [{'label': f'from {args.name}'}]}

if args.name == 's1':
    # Formatting and completion only come dynamically
    capabilities = {'codeActionProvider': {'id': 's1-code-action'}}
else:
    capabilities = {
        'codeActionProvider': True,
        'documentFormattingProvider': True,
        'completionProvider': {'triggerCharacters': [':']},
    }

run_toy_server(
    name=args.name,
    capabilities=capabilities,
    request_handlers={
        'test/send': handle_send,
        'textDocument/codeAction': answer,
        'textDocument/formatting': answer,
        'textDocument/completion': complete,
    },
)
