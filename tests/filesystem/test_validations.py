import pytest
import logging

from LogSmith import SmartLogger
from LogSmith import AsyncSmartLogger
from LogSmith import LogRecordDetails, OptionalRecordFields


def test_smartlogger_rejects_non_normalized_path(tmp_path):
    log = SmartLogger("x")

    bad = str(tmp_path) + "/../" + tmp_path.name
    with pytest.raises(ValueError):
        log.add_file(bad, "x.log")

    log.destroy()


def test_smartlogger_rejects_non_smartlogger_ancestor():
    # Simulate an ancestor logger that is NOT a SmartLogger
    ancestor_name = "root.ancestor"
    logging.Logger.manager.loggerDict[ancestor_name] = logging.getLogger("dummy")

    try:
        with pytest.raises(RuntimeError) as exc:
            SmartLogger("root.ancestor.child")

        assert "ancestor" in str(exc.value)
        assert "different type" in str(exc.value) or "does not exist" in str(exc.value)

    finally:
        # Cleanup to avoid affecting other tests
        logging.Logger.manager.loggerDict.pop(ancestor_name, None)


def test_asyncsmartlogger_rejects_non_asyncsmartlogger_ancestor():
    # Simulate an ancestor logger that is NOT an AsyncSmartLogger
    ancestor_name = "svc.api"
    logging.Logger.manager.loggerDict[ancestor_name] = logging.getLogger("dummy2")

    try:
        with pytest.raises(RuntimeError) as exc:
            AsyncSmartLogger("svc.api.child")

        assert "ancestor" in str(exc.value)
        assert "different type" in str(exc.value) or "does not exist" in str(exc.value)

    finally:
        # Cleanup
        logging.Logger.manager.loggerDict.pop(ancestor_name, None)


def test_smartlogger_rejects_duplicate_name():
    name = "duplicate.smart"

    # Simulate an existing logger with that name
    logging.Logger.manager.loggerDict[name] = logging.getLogger("dummy_smart")

    try:
        with pytest.raises(RuntimeError) as exc:
            SmartLogger(name)

        assert "already in use" in str(exc.value)

    finally:
        # Cleanup
        logging.Logger.manager.loggerDict.pop(name, None)


def test_asyncsmartlogger_rejects_duplicate_name():
    name = "duplicate.async"

    # Simulate an existing logger with that name
    logging.Logger.manager.loggerDict[name] = logging.getLogger("dummy_async")

    try:
        with pytest.raises(RuntimeError) as exc:
            AsyncSmartLogger(name)

        assert "already in use" in str(exc.value)

    finally:
        # Cleanup
        logging.Logger.manager.loggerDict.pop(name, None)


def test_message_parts_order_rejects_timestamp():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(logger_name=True),
            message_parts_order=["timestamp", "logger_name", "level"]
        )

    assert "timestamp" in str(exc.value)


def test_message_parts_order_rejects_message():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(logger_name=True),
            message_parts_order=["logger_name", "message", "level"]
        )

    assert "message" in str(exc.value)


def test_message_parts_order_missing_level_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(logger_name=True),
            message_parts_order=["logger_name"]  # missing "level"
        )

    assert "level" in str(exc.value)


def test_message_parts_order_level_appears_twice_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(logger_name=True),
            message_parts_order=["level", "logger_name", "level"]  # duplicated
        )

    assert "level" in str(exc.value)


def test_optional_fields_without_message_parts_order_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(logger_name=True),
            message_parts_order=None  # missing but required
        )

    assert "message_parts_order" in str(exc.value)


def test_message_parts_order_without_optional_fields_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=None,          # simple mode
            message_parts_order=["level"]         # illegal in simple mode
        )

    assert "message_parts_order" in str(exc.value)


def test_message_parts_order_exc_info_without_flag_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(
                logger_name=True,   # enable strict mode
                exc_info=False      # exc_info disabled
            ),
            message_parts_order=[
                "logger_name",
                "level",
                "exc_info"          # illegal because exc_info flag is False
            ]
        )

    assert "exc_info" in str(exc.value)


def test_message_parts_order_stack_info_without_flag_raises():
    with pytest.raises(ValueError) as exc:
        LogRecordDetails(
            optional_record_fields=OptionalRecordFields(
                logger_name=True,   # enable strict mode
                stack_info=False    # stack_info disabled
            ),
            message_parts_order=[
                "logger_name",
                "level",
                "stack_info"        # illegal because stack_info flag is False
            ]
        )

    assert "stack_info" in str(exc.value)
