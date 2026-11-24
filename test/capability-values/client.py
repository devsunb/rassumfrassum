#!/usr/bin/env python
"""
Test that an empty options object {} advertises a capability and
false doesn't.
"""

import argparse
import asyncio

from rassumfrassum.test2 import LspTestEndpoint, log

parser = argparse.ArgumentParser()
parser.add_argument('--trigger', action='store_true')
args = parser.parse_args()

async def trigger(client):
    # A completionProvider of true, which has no triggerCharacters,
    # must not keep a triggered completion from being answered
    req_id = await client.request('textDocument/completion', {
        'textDocument': {'uri': 'file:///test.py'},
        'position': {'line': 0, 'character': 0},
        'context': {'triggerKind': 2, 'triggerCharacter': '.'}
    })
    await client.read_response(req_id)
    log("client", "triggered completion was answered")

async def main():
    client = await LspTestEndpoint.create()
    await client.initialize()

    if args.trigger:
        await trigger(client)
        await client.byebye()
        return

    req_id = await client.request('textDocument/codeAction', {
        'textDocument': {'uri': 'file:///test.py'},
        'range': {
            'start': {'line': 0, 'character': 0},
            'end': {'line': 0, 'character': 10}
        },
        'context': {'diagnostics': []}
    })
    response = await client.read_response(req_id)
    titles = sorted(a['title'] for a in response['result'])
    assert titles == ['Fix from s1', 'Fix from s2'], \
        f"Expected code actions from s1 ({{}}) and s2 (true), got {titles}"
    log("client", f"codeAction went to s1 and s2: {titles}")

    req_id = await client.request('textDocument/completion', {
        'textDocument': {'uri': 'file:///test.py'},
        'position': {'line': 0, 'character': 0}
    })
    response = await client.read_response(req_id)
    assert 'result' in response, \
        f"Expected completions from s1 ({{}}), got {response}"
    labels = [i['label'] for i in response['result']['items']]
    assert labels == ['from s1'], \
        f"Expected completions only from s1 ({{}}), got {labels}"
    log("client", f"completion went to s1: {labels}")

    req_id = await client.request('textDocument/definition', {
        'textDocument': {'uri': 'file:///test.py'},
        'position': {'line': 0, 'character': 0}
    })
    response = await client.read_response(req_id)
    # Aggregated results come back as LocationLink, single ones as is
    uris = sorted(d.get('targetUri') or d['uri']
                  for d in response['result'])
    assert uris == ['file:///s2.py'], \
        f"Expected a definition only from s2 (s1 has false), got {uris}"
    log("client", f"definition went only to s2: {uris}")

    await client.byebye()

if __name__ == '__main__':
    asyncio.run(main())
