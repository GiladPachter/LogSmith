from pathlib import Path


def make_smart_logger(name: str, level: int, log_dir: Path | None = None):
    from LogSmith import SmartLogger  # type: ignore

    logger = SmartLogger(name, level=level)
    logger.add_console()
    if log_dir is not None:
        logger.add_file(log_dir=str(log_dir), logfile_name=f"{name}.log")
    return logger


async def make_async_logger(name: str, level: int, log_dir: Path | None = None):
    from LogSmith import AsyncSmartLogger  # type: ignore

    logger = AsyncSmartLogger(name, level=level)
    logger.add_console()
    if log_dir is not None:
        logger.add_file(log_dir=str(log_dir), logfile_name=f"{name}.log")
    return logger
