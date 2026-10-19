#!/usr/bin/env python
"""
Test that didChange on one file doesn't clear diagnostics for other files.

Regression test for bug where didChange cleanup deleted ALL dispatched
aggregations, causing other files' diagnostics to be reset to empty.
"""

import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log, scaled_timeout


async def main():
    """Test that diagnostics persist for unchanged files."""

    client = await LspTestEndpoint.create()

    # Initialize with workspace support so ruff tracks files properly
    init_caps = {
        'workspace': {
            'workspaceFolders': True,
        }
    }
    # Pin Ruff's rules: its defaults change between releases (0.17
    # dropped E703, the unnecessary semicolon in fileA)
    _ = await client.initialize(
        capabilities=init_caps,
        rootUri='file:///tmp',
        initializationOptions={'settings': {'lint': {'select': ['E703']}}},
    )

    # Open file A with a typo
    await client.notify('textDocument/didOpen', {
        'textDocument': {
            'uri': 'file:///tmp/fileA.py',
            'version': 0,
            'languageId': 'python',
            'text': '# comment with typo: speling\nBLA=str;\n'
        }
    })

    # Open file B with a typo
    await client.notify('textDocument/didOpen', {
        'textDocument': {
            'uri': 'file:///tmp/fileB.py',
            'version': 0,
            'languageId': 'python',
            'text': '# comment with typo: speling\n'
        }
    })

    A = 'file:///tmp/fileA.py'
    B = 'file:///tmp/fileB.py'
    # Diagnostics sources each file settles on
    EXPECTED = {
        A: ['Codebook', 'Codebook', 'Ruff'],
        B: ['Codebook'],
    }
    diagnostics_by_uri = {}

    def sources(uri):
        return sorted(d['source'] for d in diagnostics_by_uri.get(uri, []))

    async def collect_diags(until=None):
        """Collect diagnostic notifications, stopping once UNTIL() holds."""
        while not (until and until()):
            payload = await client.read_notification(
                'textDocument/publishDiagnostics'
            )
            uri = payload['uri']
            diags = payload.get('diagnostics', [])
            diagnostics_by_uri[uri] = diags
            log("client", f"Got {len(diags)} diagnostic(s) for {uri}")

    # Servers can be slow to report under load, so wait for the
    # expected diagnostics instead of for a fixed time
    await asyncio.wait_for(
        collect_diags(lambda: all(sources(u) == e for u, e in EXPECTED.items())),
        timeout=scaled_timeout(10),
    )
    a_before = diagnostics_by_uri[A]
    b_before = diagnostics_by_uri[B]

    # Now change fileA
    await client.notify('textDocument/didChange', {
        'textDocument': {
            'uri': 'file:///tmp/fileA.py',
            'version': 1
        },
        'contentChanges': [{'text': '# changed comment, still has typo: speling\nBLA=str;\n'}]
    })
    await client.notify('workspace/didChangeWatchedFiles', {
        "changes": [
            {
                "uri": 'file:///tmp/fileA.py',
                "type": 2
            }
        ]
    })
    # Save fileA
    await client.notify('textDocument/didSave', {
        'textDocument': {
            'uri': 'file:///tmp/fileA.py'
        }
    })

    # Wait for fileA's complete re-report, then keep listening a bit,
    # since a wrongly cleared fileB could be published after it
    del diagnostics_by_uri[A]
    await asyncio.wait_for(
        collect_diags(lambda: sources(A) == EXPECTED[A]),
        timeout=scaled_timeout(10),
    )
    try:
        await asyncio.wait_for(collect_diags(), timeout=scaled_timeout(1.5))
    except asyncio.TimeoutError:
        pass

    assert diagnostics_by_uri[B] == b_before, "fileB should have kept diagnostics!"
    assert sources(A) == sorted(d['source'] for d in a_before), (
        "fileA should have kept diagnostics!"
    )

    await client.byebye()

if __name__ == '__main__':
    asyncio.run(main())
