#!/usr/bin/env python
"""
Server that can delay its initialize response and provide definitions.
"""

import argparse
import time

from rassumfrassum.test2 import run_toy_server, log

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument(
    '--initialize-delay',
    type=int,
    default=0,
    help='Delay in milliseconds before responding to initialize',
)
parser.add_argument(
    '--definition',
    action='store_true',
    help='Advertise and answer textDocument/definition',
)
args = parser.parse_args()


def handle_initialize(msg_id, params):
    """Handle initialize with optional delay."""
    if args.initialize_delay > 0:
        log(
            args.name,
            f"Delaying initialize response by {args.initialize_delay}ms",
        )
        time.sleep(args.initialize_delay / 1000.0)

    capabilities = {'textDocumentSync': 2}
    if args.definition:
        capabilities['definitionProvider'] = True
    return {
        'capabilities': capabilities,
        'serverInfo': {'name': args.name, 'version': '1.0.0'},
    }


def handle_definition(msg_id, params):
    return [
        {
            'uri': f"file:///tmp/{args.name}.py",
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 0, 'character': 1},
            },
        }
    ]


run_toy_server(
    name=args.name,
    request_handlers={
        'initialize': handle_initialize,
        'textDocument/definition': handle_definition,
    },
)
