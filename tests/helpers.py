import logging


def read_file(path):
    return path.read_text(encoding="utf-8")


class DummyHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


