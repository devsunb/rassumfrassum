#!/usr/bin/env python
"""
Test that rass forwards 'exit' to its servers and exits even if the
client keeps its end of the connection open, as Eglot does.
"""

import asyncio
import os
import sys
from pathlib import Path

from rassumfrassum.json import read_message
from rassumfrassum.test2 import LspTestEndpoint, log, scaled_timeout

async def main():
    client = await LspTestEndpoint.create()
    await client.initialize()

    req_id = await client.request('shutdown')
    await client.read_response(req_id)
    await client.notify('exit', {})

    # Don't close our stdout, so rass can't rely on seeing EOF.  rass
    # exiting closes its stdout, which shows up here as EOF.
    try:
        msg = await asyncio.wait_for(read_message(client.reader), timeout=scaled_timeout(2))
    except asyncio.TimeoutError:
        raise AssertionError("rass still running after 'exit'")
    assert msg is None, f"Expected EOF after 'exit', got {msg}"
    log("client", "rass exited on 'exit'")

    # rass exits after its servers, so they're done by now
    for name in ('s1', 's2'):
        marker = Path(f'{name}.exited')
        assert marker.exists(), f"{name} didn't get 'exit'"
        marker.unlink()
    log("client", "servers got 'exit'")

    # Same Windows kludge as LspTestEndpoint.byebye.
    if sys.platform == 'win32':
        os._exit(0)
    else:
        sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())
