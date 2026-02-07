"""
Timeouts for handshake, block requests, tracker calls. Prevents deadlocks.
"""
import asyncio


async def with_timeout(coro, timeout=10):
    """Run coroutine with timeout; return None on TimeoutError."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return None
