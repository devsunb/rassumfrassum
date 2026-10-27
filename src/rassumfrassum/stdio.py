"""Cross-platform asyncio-compatible stdin/stdout.

On Windows, this is unfortunately more complicated
"""

import asyncio
import os
import platform
import socket
import sys
import threading


async def create_stdin_reader() -> asyncio.StreamReader:
    """Create an asyncio StreamReader for stdin.

    On Windows: Uses blocking reads in a daemon thread.
    On Unix: Direct connection to sys.stdin.
    """
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()

    if platform.system() == 'Windows':
        # Windows: Use blocking reads to avoid pipe issues.  Read in a
        # daemon thread, not in the default executor: asyncio.run()
        # joins executor threads on the way out, so a read blocked on
        # a client that keeps stdin open would keep us from exiting.
        # Read the file descriptor, not sys.stdin.buffer, whose lock
        # the blocked read would hold during interpreter shutdown.
        fd = sys.stdin.fileno()

        def read_stdin_loop():
            while True:
                try:
                    # Returns whatever is available, without waiting
                    # for a full buffer.
                    chunk = os.read(fd, 4096)
                except Exception:
                    chunk = b''
                try:
                    if not chunk:
                        loop.call_soon_threadsafe(reader.feed_eof)
                        return
                    loop.call_soon_threadsafe(reader.feed_data, chunk)
                except RuntimeError:
                    # The loop is closed: we're exiting.
                    return

        threading.Thread(target=read_stdin_loop, daemon=True).start()
        return reader
    else:
        # Unix: Direct connection works fine
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        return reader


class _WindowsStdoutWriter:
    """A StreamWriter-like wrapper for Windows stdout using run_in_executor."""

    def __init__(self, loop):
        self._loop = loop
        self._buffer = bytearray()

    def write(self, data):
        """Add data to the buffer."""
        self._buffer.extend(data)

    async def drain(self):
        """Flush the buffer to stdout using run_in_executor."""
        if not self._buffer:
            return

        data = bytes(self._buffer)
        self._buffer.clear()

        def blocking_write(data):
            """Blocking write to stdout buffer - runs in thread pool."""
            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except Exception:
                pass

        await self._loop.run_in_executor(None, blocking_write, data)

    def close(self):
        """Close the writer."""
        pass

    async def wait_closed(self):
        """Wait for close to complete."""
        pass


async def create_stdout_writer() -> asyncio.StreamWriter:
    """Create an asyncio StreamWriter for stdout.

    On Windows: Uses run_in_executor with blocking writes.
    On Unix: Direct connection to sys.stdout.
    """
    loop = asyncio.get_event_loop()

    if platform.system() == 'Windows':
        # Windows: Use custom wrapper with run_in_executor
        return _WindowsStdoutWriter(loop)
    else:
        # Unix: Direct connection works fine
        transport, protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(transport, protocol, None, loop)
        return writer
