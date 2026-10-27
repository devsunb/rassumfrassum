#!/usr/bin/env python
"""
Server whose codeActionProvider and definitionProvider values are
given on the command line as JSON.
"""

import argparse
import json

from rassumfrassum.test2 import run_toy_server

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--code-action', type=json.loads, required=True,
                    help='JSON value of codeActionProvider')
parser.add_argument('--definition', type=json.loads, required=True,
                    help='JSON value of definitionProvider')
parser.add_argument('--completion', type=json.loads,
                    help='JSON value of completionProvider, if any')
args = parser.parse_args()

def handle_code_action(msg_id, params):
    return [{'title': f'Fix from {args.name}', 'kind': 'quickfix'}]

def handle_completion(msg_id, params):
    return {'isIncomplete': False, 'items': [{'label': f'from {args.name}'}]}

def handle_definition(msg_id, params):
    # Give each server its own line, so aggregation keeps them apart
    line = int(args.name.lstrip('s'))
    return [{
        'uri': f'file:///{args.name}.py',
        'range': {
            'start': {'line': line, 'character': 0},
            'end': {'line': line, 'character': 10}
        }
    }]

capabilities = {
    'codeActionProvider': args.code_action,
    'definitionProvider': args.definition,
}
if args.completion is not None:
    capabilities['completionProvider'] = args.completion

run_toy_server(
    name=args.name,
    capabilities=capabilities,
    request_handlers={
        'textDocument/codeAction': handle_code_action,
        'textDocument/completion': handle_completion,
        'textDocument/definition': handle_definition,
    }
)
