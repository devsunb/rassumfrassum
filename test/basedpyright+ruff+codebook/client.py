#!/usr/bin/env python
"""
Test client for basedpyright + ruff + codebook servers.
Tests three-server diagnostic aggregation with tardy updates using async.
"""

import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log, scaled_timeout

async def main():
    """Test three-server diagnostics with tardy updates."""

    client = await LspTestEndpoint.create()
    # Pin Ruff's rules: its defaults change between releases (0.17
    # dropped E703, the unnecessary semicolons counted below)
    await client.initialize(
        rootUri='file:///tmp',
        initializationOptions={'settings': {'lint': {'select': ['E703']}}},
    )

    # Open documents with errors
    log("client", "Opening test1.py")
    await client.notify('textDocument/didOpen', {
        'textDocument': {
            'uri': 'file:///tmp/test1.py',
            'version': 1,
            'languageId': 'python',
            'text': '''\
# This is a tset comment
def foo(x: int) -> int:
    return x;

foo("wrong");  # Type error: passing str to int
'''
        }
    })

    log("client", "Opening test2.py")
    await client.notify('textDocument/didOpen', {
        'textDocument': {
            'uri': 'file:///tmp/test2.py',
            'version': 1,
            'languageId': 'python',
            'text': '''\
# Speling mistake here
def bar(s: str) -> str:
    return s.upper();

bar(42);  # Type error: passing int to str
'''
        }
    })

    # Diagnostics sources each file settles on
    EXPECTED = {'Ruff': 2, 'Codebook': 1, 'basedpyright': 2}
    URIS = ['file:///tmp/test1.py', 'file:///tmp/test2.py']
    diagnostics_by_uri = {}
    log("client", "Waiting for diagnostics (including tardy)...")

    def settled():
        def count(uri):
            sources = {}
            for d in diagnostics_by_uri.get(uri, []):
                sources[d.get('source')] = sources.get(d.get('source'), 0) + 1
            return sources
        return all(count(uri) == EXPECTED for uri in URIS)

    async def collect_diags():
        """Collect diagnostic notifications."""
        while not settled():
            payload = await client.read_notification('textDocument/publishDiagnostics')
            uri = payload['uri']
            diags = payload.get('diagnostics', [])

            old_count = len(diagnostics_by_uri.get(uri, []))
            diagnostics_by_uri[uri] = diags

            if old_count > 0:
                log("client", f"Got {len(diags)} diagnostic(s) for {uri} (replacing {old_count})")
            else:
                log("client", f"Got {len(diags)} diagnostic(s) for {uri}")

    # Servers can be slow to report under load, so wait for the
    # expected diagnostics instead of for a fixed time
    try:
        await asyncio.wait_for(collect_diags(), timeout=scaled_timeout(15))
    except asyncio.TimeoutError:
        log("client", "Timeout reached, done collecting diagnostics")

    # Report final diagnostics
    for uri in URIS:
        diags = diagnostics_by_uri.get(uri, [])
        log("client", f"\n{uri}: {len(diags)} total diagnostic(s)")

        sources = {}
        for diag in diags:
            source = diag.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            log("client", f"  [{source}] {diag.get('message', '')[:60]}")

        log("client", f"  Sources: {sources}")

        # Assertions: expect diagnostics from all 3 servers
        assert len(diags) == 5, f"Expected 5 diagnostics for {uri}, got {len(diags)}"
        assert sources.get('Ruff', 0) == 2, f"Expected 2 Ruff diagnostics for {uri}"
        assert sources.get('Codebook', 0) == 1, f"Expected 1 Codebook diagnostic for {uri}"
        assert sources.get('basedpyright', 0) == 2, f"Expected 2 basedpyright diagnostics for {uri}"

    await client.byebye()

if __name__ == '__main__':
    asyncio.run(main())
