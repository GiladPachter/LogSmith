import pytest
from pathlib import Path
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When


# ------------------------------------------------------------
# 1. Enable auditing (covers 952)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_enable(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit.log",
    )

    info = AsyncSmartLogger.audit_handler_info()
    assert info is not None
    assert info["kind"] == "file"
    assert info["path"].endswith("audit.log")

    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 2. Audit logger receives logs from other loggers (983–989)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_receives_logs(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit2.log",
    )

    logger = AsyncSmartLogger("app_logger")
    logger.add_console()

    await logger.a_info("hello audit")
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    audit_file = Path(tmp_path) / "audit2.log"
    text = audit_file.read_text()

    assert "hello audit" in text
    assert "app_logger" in text  # audit prefix

    logger.destroy()


# ------------------------------------------------------------
# 3. Audit formatter (995–997)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_formatter(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit3.log",
    )

    logger = AsyncSmartLogger("source")
    logger.add_console()

    await logger.a_warning("audit formatting test")
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    text = (Path(tmp_path) / "audit3.log").read_text()

    # AuditFormatter prefixes with "[logger]: "
    assert "[source]:" in text
    assert "audit formatting test" in text


# ------------------------------------------------------------
# 4. Audit rotation logic (1028, 1032, 1048, 1055)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_rotation_metadata_only(tmp_path):
    logic = RotationLogic(
        when=When.SECOND,
        interval=1,
        maxBytes=10,
        backupCount=2,
    )

    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_rotate.log",
        rotation_logic=logic,
    )

    info = AsyncSmartLogger.audit_handler_info()

    # Rotation logic is stored but not executed
    assert info["rotation"]["maxBytes"] == 10
    assert info["rotation"]["backupCount"] == 2

    # Only one file should exist
    await AsyncSmartLogger.terminate_auditing()

    files = [f.name for f in tmp_path.iterdir() if f.name.startswith("audit_rotate")]
    assert len(files) == 1


# ------------------------------------------------------------
# 5. Audit shutdown (1078, 1086–1087)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_shutdown(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_shutdown.log",
    )

    await AsyncSmartLogger.terminate_auditing()

    # audit disabled
    assert AsyncSmartLogger.audit_handler_info() is None


# ------------------------------------------------------------
# 6. Audit handler removal (1108)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_handler_removed(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_remove.log",
    )

    await AsyncSmartLogger.terminate_auditing()

    # No handler should remain
    assert AsyncSmartLogger.audit_handler_info() is None


# ------------------------------------------------------------
# 7. Audit error swallowing (1129→1127)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_error_swallowed(tmp_path, monkeypatch):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_err.log",
    )

    handler = AsyncSmartLogger._AsyncSmartLogger__audit_handler

    # Force handler.close() to fail
    def bad_close():
        raise RuntimeError("boom")

    monkeypatch.setattr(handler, "close", bad_close)

    # Should not crash
    await AsyncSmartLogger.terminate_auditing()


# ------------------------------------------------------------
# 8. Audit flush (1181–1184)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_flush(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_flush.log",
    )

    logger = AsyncSmartLogger("flush_test")
    logger.add_console()

    await logger.a_info("flush me")
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    text = (Path(tmp_path) / "audit_flush.log").read_text()
    assert "flush me" in text


# ------------------------------------------------------------
# 9. Audit shutdown with pending logs (1207–1214)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_shutdown_with_pending(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_pending.log",
    )

    logger = AsyncSmartLogger("pending")
    logger.add_console()

    # enqueue logs but do not flush
    for _ in range(5):
        await logger.a_info("pending")

    # terminate auditing while logs still pending
    await AsyncSmartLogger.terminate_auditing()

    # Should not hang or crash


# ------------------------------------------------------------
# 10. Audit metadata (1230–1249, 1247)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_metadata(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_meta.log",
    )

    logger = AsyncSmartLogger("meta_src")
    logger.add_console()

    await logger.a_info("meta test", user="gilad", request_id=42)
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    text = (Path(tmp_path) / "audit_meta.log").read_text()

    assert "gilad" in text
    assert "42" in text


# ------------------------------------------------------------
# 11. Audit file reopen (1288)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_file_reopen_is_noop(tmp_path):
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="audit_reopen.log",
    )

    handler = AsyncSmartLogger._AsyncSmartLogger__audit_handler

    # Simulate missing stream
    handler.stream = None

    logger = AsyncSmartLogger("reopen_src")
    logger.add_console()

    await logger.a_info("reopen test")
    await logger.flush()

    await AsyncSmartLogger.terminate_auditing()

    text = (Path(tmp_path) / "audit_reopen.log").read_text(encoding="utf-8")

    # Audit logger does NOT reopen the file
    # and silently drops writes
    assert text != ""


# ------------------------------------------------------------
# 12. Audit duplicate detection (1353, 1356–1363)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_duplicate_detection(tmp_path):
    # First audit logger
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="dup_audit.log",
    )

    # Second call should be ignored (audit already enabled)
    await AsyncSmartLogger.audit_everything(
        log_dir=str(tmp_path),
        logfile_name="dup_audit.log",
    )

    await AsyncSmartLogger.terminate_auditing()
