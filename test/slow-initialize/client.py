#!/usr/bin/env python
"""
Test that rass waits for a server that is slow to answer initialize.

s2 takes longer than the usual 3000ms aggregation timeout, but within
the initialize timeout, so the client must see its capabilities and get
requests routed to it.
"""

import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log


async def main():
    client = await LspTestEndpoint.create()
    response = await client.initialize()
    caps = response['result']['capabilities']
    assert caps.get('definitionProvider'), f"Expected s2's capabilities: {caps}"

    # Only s2 provides definitions
    req_id = await client.request(
        'textDocument/definition',
        {
            'textDocument': {'uri': 'file:///tmp/test.py'},
            'position': {'line': 0, 'character': 0},
        },
    )
    response = await client.read_response(req_id)
    log("client", f"Got definition response: {response}")
    result = response.get('result')
    assert result and result[0]['uri'] == 'file:///tmp/s2.py', (
        f"Expected s2's definition, got {response}"
    )

    await client.byebye()


if __name__ == '__main__':
    asyncio.run(main())
