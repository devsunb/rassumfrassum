#!/usr/bin/env python
"""Test that client/unregisterCapability removes the capability from
`Server.caps` so subsequent routing skips the unregistering server."""

import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log


async def main():
    client = await LspTestEndpoint.create()
    await client.initialize()

    # s1 sent client/unregisterCapability for textDocument/codeAction
    # immediately after initialized.  Acknowledge so rass forwards a
    # response back to it.
    req_id, params = await client.read_request('client/unregisterCapability')
    log("client", f"Got server unregister request: id={req_id} params={params}")
    await client.respond(req_id, None)

    rid = await client.request('textDocument/codeAction', {
        'textDocument': {'uri': 'file:///test.py'},
        'range': {
            'start': {'line': 0, 'character': 0},
            'end': {'line': 0, 'character': 10},
        },
        'context': {'diagnostics': []},
    })

    response = await client.read_response(rid)
    actions = response['result']
    log("client", f"Got {len(actions)} code actions: {actions}")

    titles = [a['title'] for a in actions]
    assert titles == ['Fix from s2'], (
        f"Expected only s2 action after s1 unregistered codeAction, "
        f"got {titles}"
    )

    log("client", "OK: codeAction routed only to remaining capable server")
    await client.byebye()


if __name__ == '__main__':
    asyncio.run(main())
