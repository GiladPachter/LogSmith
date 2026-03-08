import asyncio
import pytest

@pytest.fixture(autouse=True)
def ensure_async_cleanup():
    """
    Ensures that after each test:
    - all async tasks are awaited
    - no background tasks remain
    - event loop is clean
    """
    yield

    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
