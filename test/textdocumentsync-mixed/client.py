#!/usr/bin/env python
"""
Test mixed text sync kinds (#55): primary incremental, secondary full.

rass must advertise Incremental to the client, translate to Full for
the full-sync server, and turn range-less resync changes into a
didClose/didOpen pair for a ruby-lsp lookalike, which rejects them.
The servers report their mirrors and objections on didSave.
"""

import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log

URI = 'file:///tmp/test.md'
OPEN = 'line0\nline1\nline2\n'
MID = 'line0\nline1X\nline2!\n'
RESYNC = 'totally\ndifferent\n'
SERVERS = ('s1', 's2', 'Ruby LSP')


async def check_reports(client, text):
    """Read each server's didSave report; check its mirror is TEXT."""
    reports = {}
    for _ in SERVERS:
        r = await asyncio.wait_for(
            client.read_notification('rass-test/docState'), timeout=5
        )
        log('client', f"report: {r}")
        assert not r['errors'], r['errors']
        assert r['doc'] == text, (
            f"{r['server']} expected {text!r}, got {r['doc']!r}"
        )
        reports[r['server']] = r
    return reports


async def main():
    client = await LspTestEndpoint.create()
    init_response = await client.initialize()

    caps = init_response['result']['capabilities']
    sync = caps.get('textDocumentSync')
    log("client", f"Advertised textDocumentSync={sync}")
    assert isinstance(sync, dict) and sync.get('change') == 2, (
        f"Expected Incremental (change=2), got: {sync}"
    )

    await client.notify(
        'textDocument/didOpen',
        {
            'textDocument': {
                'uri': URI,
                'languageId': 'markdown',
                'version': 1,
                'text': OPEN,
            }
        },
    )

    # Two forward-sequential ranged changes (as an incremental client
    # would send)
    await client.notify(
        'textDocument/didChange',
        {
            'textDocument': {'uri': URI, 'version': 2},
            'contentChanges': [
                {
                    'range': {
                        'start': {'line': 1, 'character': 0},
                        'end': {'line': 1, 'character': 5},
                    },
                    'text': 'line1X',
                },
                {
                    'range': {
                        'start': {'line': 2, 'character': 5},
                        'end': {'line': 2, 'character': 5},
                    },
                    'text': '!',
                },
            ],
        },
    )
    await client.notify(
        'textDocument/didSave',
        {
            'textDocument': {'uri': URI},
            'text': MID,
        },
    )
    await check_reports(client, MID)

    # Range-less "resync" change: forwarded verbatim to s1, but rass
    # must reopen the document for 'Ruby LSP'
    await client.notify(
        'textDocument/didChange',
        {
            'textDocument': {'uri': URI, 'version': 3},
            'contentChanges': [{'text': RESYNC}],
        },
    )
    await client.notify(
        'textDocument/didSave',
        {
            'textDocument': {'uri': URI},
            'text': RESYNC,
        },
    )
    reports = await check_reports(client, RESYNC)
    assert reports['s1']['rangeless'] == 1, reports['s1']
    assert reports['Ruby LSP']['opens'] == 2, reports['Ruby LSP']

    log("client", "All assertions passed")
    await client.byebye()


if __name__ == '__main__':
    asyncio.run(main())
