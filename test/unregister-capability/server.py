#!/usr/bin/env python
"""Server for unregister-capability test."""

import argparse

from rassumfrassum.test2 import run_toy_server, log
from rassumfrassum.json import write_message_sync

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument('--unregister-codeaction', action='store_true')
args = parser.parse_args()


def handle_initialized(_params):
    if args.unregister_codeaction:
        log(args.name, "Sending client/unregisterCapability for codeAction")
        write_message_sync({
            'jsonrpc': '2.0',
            'id': 'unregister-1',
            'method': 'client/unregisterCapability',
            'params': {
                'unregisterations': [{
                    'id': f'{args.name}_code_action',
                    'method': 'textDocument/codeAction',
                }],
            },
        })


def handle_codeaction(_req_id, _params):
    return [{'title': f'Fix from {args.name}'}]


run_toy_server(
    name=args.name,
    capabilities={'codeActionProvider': True},
    request_handlers={'textDocument/codeAction': handle_codeaction},
    notification_handlers={'initialized': handle_initialized},
)
