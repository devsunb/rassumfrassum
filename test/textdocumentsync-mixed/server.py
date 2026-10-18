#!/usr/bin/env python
"""
Toy server with configurable textDocumentSync kind, tracking document
state.

Tracks the document it's told about, applying didChange content
changes to a mirror, and notes any change whose shape it doesn't
accept: full-sync servers take a single range-less change, and a
server named 'Ruby LSP' takes only ranged ones, like the real
ruby-lsp.  On didSave, sends the mirror, those notes and some counters
upstream in a 'rass-test/docState' notification so the client can
check them.  (A server that exits on a failed check doesn't reliably
make run.sh fail.)
"""

import argparse

from rassumfrassum.json import write_message_sync
from rassumfrassum.test2 import run_toy_server

parser = argparse.ArgumentParser()
parser.add_argument('--name', required=True)
parser.add_argument(
    '--text-document-sync',
    type=int,
    default=2,
    help='textDocumentSync kind: 1=Full, 2=Incremental',
)
args = parser.parse_args()

sync_kind = args.text_document_sync
state = {'doc': '', 'errors': [], 'opens': 0, 'rangeless': 0}


def offset(text, pos):
    """Offset of an LSP position (code points = UTF-16 units here)."""
    return (
        sum(len(l) + 1 for l in text.split('\n')[: pos['line']])
        + pos['character']
    )


def apply_changes(text, changes):
    """Apply didChange content changes in order (see LSP spec)."""
    for change in changes:
        new = change.get('text', '')
        if (r := change.get('range')) is None:
            text = new
        else:
            start = offset(text, r['start'])
            end = offset(text, r['end'])
            text = text[:start] + new + text[end:]
    return text


def did_open(params):
    state['doc'] = params['textDocument']['text']
    state['opens'] += 1


def did_close(params):
    state['doc'] = ''


def did_change(params):
    changes = params['contentChanges']
    if sync_kind == 1:
        if not (len(changes) == 1 and 'range' not in changes[0]):
            state['errors'].append(f"full-sync server got {changes}")
    elif args.name == 'Ruby LSP':
        if not all('range' in c for c in changes):
            state['errors'].append(f"ranged-only server got {changes}")
    state['rangeless'] += any('range' not in c for c in changes)
    state['doc'] = apply_changes(state['doc'], changes)


def did_save(params):
    write_message_sync(
        {
            'jsonrpc': '2.0',
            'method': 'rass-test/docState',
            'params': {'server': args.name, **state},
        }
    )


run_toy_server(
    name=args.name,
    capabilities={
        'textDocumentSync': {
            'change': sync_kind,
            'openClose': True,
            'save': True,
        },
        'hoverProvider': True,
    },
    notification_handlers={
        'textDocument/didOpen': did_open,
        'textDocument/didClose': did_close,
        'textDocument/didChange': did_change,
        'textDocument/didSave': did_save,
    },
)
