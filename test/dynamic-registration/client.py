#!/usr/bin/env python
"""
Test that rass routes by what servers register and unregister
dynamically, and unregisters a static capability only by its id.
"""

import asyncio

from rassumfrassum.json import write_message
from rassumfrassum.test2 import LspTestEndpoint, log

DOC = {'uri': 'file:///test.py'}

async def main():
    client = await LspTestEndpoint.create()
    await client.initialize()
    await client.notify('textDocument/didOpen', {'textDocument': {
        **DOC, 'languageId': 'python', 'version': 1, 'text': ''}})

    async def s1_sends(method, params, accept=True):
        # s1 is the primary server, so it gets 'test/send'
        send_id = await client.request('test/send', {
            'method': method, 'params': params})
        req_id, _ = await client.read_request(method)
        if accept:
            await client.respond(req_id, None)
        else:
            await write_message(client.writer, {
                'jsonrpc': '2.0', 'id': req_id,
                'error': {'code': -32600, 'message': 'refused'}})
        await client.read_response(send_id)

    async def register(*regs, accept=True):
        await s1_sends('client/registerCapability', {'registrations': [
            {'id': i, 'method': m, 'registerOptions': o} for i, m, o in regs]},
            accept)

    async def unregister(*unregs):
        await s1_sends('client/unregisterCapability', {'unregisterations': [
            {'id': i, 'method': m} for i, m in unregs]})

    async def who(method, params):
        req_id = await client.request(method, {'textDocument': DOC, **params})
        result = (await client.read_response(req_id)).get('result') or []
        if isinstance(result, dict):
            result = result['items']
        return sorted(r.get('title') or r.get('label') for r in result)

    async def formatting():
        return await who('textDocument/formatting', {
            'options': {'tabSize': 4, 'insertSpaces': True}})

    async def code_action():
        return await who('textDocument/codeAction', {
            'range': {'start': {'line': 0, 'character': 0},
                      'end': {'line': 0, 'character': 0}},
            'context': {'diagnostics': []}})

    async def triggered_completion():
        return await who('textDocument/completion', {
            'position': {'line': 0, 'character': 0},
            'context': {'triggerKind': 2, 'triggerCharacter': '.'}})

    fmt = 'textDocument/formatting'
    ca = 'textDocument/codeAction'
    cmp = 'textDocument/completion'

    assert await formatting() == ['from s2']

    await register(('f0', fmt, {}), accept=False)
    assert await formatting() == ['from s2']
    log("client", "a registration the client refused is ignored")

    await register(('f0', fmt, {'documentSelector': [{'language': 'json'}]}),
                   ('k0', cmp, {'documentSelector': [{'language': 'json'}],
                                'triggerCharacters': ['.']}))
    assert await formatting() == ['from s2']
    assert await triggered_completion() == ['from s2']
    log("client", "a registration for other documents is ignored")

    await register((['x'], fmt, {}))
    assert await code_action() == ['from s1', 'from s2']
    log("client", "a malformed registration is ignored")

    await register(('f1', fmt, {}), ('f2', fmt, {}))
    assert await formatting() == ['from s1']
    log("client", "a registration routes to the server")

    await unregister(('f1', fmt))
    assert await formatting() == ['from s1']
    await unregister(('f2', fmt))
    assert await formatting() == ['from s2']
    log("client", "an unregistration drops that registration only")

    await unregister(('unknown', ca))
    assert await code_action() == ['from s1', 'from s2']
    await unregister(('s1-code-action', ca))
    assert await code_action() == ['from s2']
    log("client", "a static capability goes only by its own id")

    await register(('c1', ca, None))
    assert await code_action() == ['from s1', 'from s2']
    log("client", "registering again brings it back")

    await register(('k1', cmp, {'triggerCharacters': ['.']}))
    assert await triggered_completion() == ['from s1']
    log("client", "registered trigger characters route completion")

    await client.byebye()

if __name__ == '__main__':
    asyncio.run(main())
