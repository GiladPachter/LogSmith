import logging

from LogSmith import SmartLogger


def read_file(path):
    return path.read_text(encoding="utf-8")


class DummyHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


# ============================================================
# Helper: isolate logger
# ============================================================
def isolated_logger(name: str) -> SmartLogger:
    logger = SmartLogger(name)
    # noinspection PyProtectedMember
    py = logger._SmartLogger__py_logger
    for h in list(py.handlers):
        py.removeHandler(h)
    return logger
