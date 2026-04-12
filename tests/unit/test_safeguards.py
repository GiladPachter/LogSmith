import pytest
import logging

from LogSmith.smartlogger import SmartLogger
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.level_registry import reset_levels_for_tests


@pytest.fixture(autouse=True)
def reset_levels():
    # Ensure a clean level registry before each test
    reset_levels_for_tests()
    yield
    reset_levels_for_tests()


@pytest.mark.parametrize("cls", [SmartLogger, AsyncSmartLogger])
def test_safeguard_rejects_internal_attribute_override(cls):
    # SmartLogger.__dict__ and AsyncSmartLogger.__dict__ both contain "level"
    with pytest.raises(ValueError):
        cls.register_level("level", 55)


@pytest.mark.parametrize("cls", [SmartLogger, AsyncSmartLogger])
def test_safeguard_rejects_duplicate_level_name(cls):
    # TRACE already exists in LEVELS
    with pytest.raises(ValueError):
        cls.register_level("TRACE", 123)


@pytest.mark.parametrize("cls", [SmartLogger, AsyncSmartLogger])
def test_safeguard_rejects_duplicate_numeric_value(cls):
    # DEBUG is numeric value 10
    with pytest.raises(ValueError):
        cls.register_level("MYDEBUG", logging.DEBUG)


@pytest.mark.parametrize("cls", [SmartLogger, AsyncSmartLogger])
def test_safeguard_rejects_negative_level_value(cls):
    with pytest.raises(ValueError):
        cls.register_level("NEGATIVE", -1)


@pytest.mark.parametrize("cls", [SmartLogger, AsyncSmartLogger])
def test_safeguard_rejects_invalid_level_name(cls):
    # Must match [A-Z][A-Z0-9_]* — lowercase is invalid
    with pytest.raises(ValueError):
        cls.register_level("badname", 55)


# ------------------------------------------------------------
# SmartLogger tests
# ------------------------------------------------------------

def test_smartlogger_raw_raises_after_retire(tmp_path):
    lg = SmartLogger("sl_raw_retire")
    lg.retire()
    with pytest.raises(RuntimeError):
        lg.raw(logging.INFO, "x")


def test_smartlogger_raw_raises_after_destroy(tmp_path):
    lg = SmartLogger("sl_raw_destroy")
    lg.destroy()
    with pytest.raises(RuntimeError):
        lg.raw(logging.INFO, "x")


def test_smartlogger_debug_raises_after_retire(tmp_path):
    lg = SmartLogger("sl_debug_retire")
    lg.retire()
    with pytest.raises(RuntimeError):
        lg.debug("x")


def test_smartlogger_debug_raises_after_destroy(tmp_path):
    lg = SmartLogger("sl_debug_destroy")
    lg.destroy()
    with pytest.raises(RuntimeError):
        lg.debug("x")


# ------------------------------------------------------------
# AsyncSmartLogger tests
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_raw_raises_after_retire(tmp_path):
    lg = AsyncSmartLogger("asl_raw_retire")
    lg.retire()
    with pytest.raises(RuntimeError):
        await lg.a_raw("x")


@pytest.mark.asyncio
async def test_async_raw_raises_after_destroy(tmp_path):
    lg = AsyncSmartLogger("asl_raw_destroy")
    await lg.shutdown()   # destroy() is sync, but shutdown is required first
    lg.destroy()
    with pytest.raises(RuntimeError):
        await lg.a_raw("x")


@pytest.mark.asyncio
async def test_async_debug_raises_after_retire(tmp_path):
    lg = AsyncSmartLogger("asl_debug_retire")
    lg.retire()
    with pytest.raises(RuntimeError):
        await lg.a_debug("x")


@pytest.mark.asyncio
async def test_async_debug_raises_after_destroy(tmp_path):
    lg = AsyncSmartLogger("asl_debug_destroy")
    await lg.shutdown()
    lg.destroy()
    with pytest.raises(RuntimeError):
        await lg.a_debug("x")


def test_asyncsmartlogger_rejects_non_asyncsmartlogger_ancestor():
    ancestor = "svc"
    child = "svc.api"

    # Insert a standard logging.Logger as the ancestor
    logging.Logger.manager.loggerDict[ancestor] = logging.getLogger("dummy_ancestor")

    try:
        with pytest.raises(RuntimeError) as exc:
            AsyncSmartLogger(child)

        # The error message should mention ancestor mismatch
        msg = str(exc.value).lower()
        assert "ancestor" in msg
        assert "different type" in msg or "does not exist" in msg

    finally:
        # Cleanup to avoid polluting global logger state
        logging.Logger.manager.loggerDict.pop(ancestor, None)


@pytest.mark.asyncio
async def test_asyncsmartlogger_raises_after_retire():
    logger = AsyncSmartLogger("retire_test")

    # Retire the logger
    logger.retire()

    # Any async logging call should now raise RuntimeError
    with pytest.raises(RuntimeError) as exc:
        await logger.a_info("this should fail")

    msg = str(exc.value).lower()
    assert "retired" in msg
    assert "cannot be used" in msg

    logger.destroy()
