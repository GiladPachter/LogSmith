import logging
from LogSmith import SmartLogger

def test_sync_audit_mirroring(tmp_path):
    main = SmartLogger("main_sync", logging.INFO)
    main.add_file(str(tmp_path), "main.log")

    audit = SmartLogger("audit_sync", logging.INFO)
    audit.add_file(str(tmp_path), "audit.log")

    SmartLogger._SmartLogger__audit_enabled = True
    SmartLogger._SmartLogger__audit_handler = audit._py_logger.handlers[0]

    main.info("hello audit sync")

    # flush both
    for h in main._py_logger.handlers:
        h.flush()
    for h in audit._py_logger.handlers:
        h.flush()

    text = (tmp_path / "audit.log").read_text()
    assert "hello audit sync" in text

    SmartLogger._SmartLogger__audit_enabled = False
    SmartLogger._SmartLogger__audit_handler = None
