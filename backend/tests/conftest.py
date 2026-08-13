"""Cross-platform pytest configuration."""

import asyncio
import sys


def pytest_asyncio_loop_factories(config, item):
    """Use the selector loop required by Psycopg's async client on Windows."""

    del config, item
    if sys.platform == "win32":
        return {"selector": asyncio.SelectorEventLoop}
    return {"default": asyncio.new_event_loop}
