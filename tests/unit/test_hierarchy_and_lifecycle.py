from LogSmith import SmartLogger


def test_logger_hierarchy_inheritance_and_override(capsys):
    levels = SmartLogger.levels()

    root = SmartLogger("myapp", level=levels["INFO"])
    root.add_console()

    api = SmartLogger("myapp.api", level=levels["NOTSET"])
    api.add_console()
    users = SmartLogger("myapp.api.users", level=levels["DEBUG"])
    users.add_console()

    # api inherits INFO, users overrides to DEBUG
    api.info("api info")
    api.debug("api debug (should be filtered)")

    users.debug("users debug")
    users.info("users info")

    out = capsys.readouterr().out
    assert "api info" in out
    assert "api debug" not in out
    assert "users debug" in out
    assert "users info" in out


def test_handlers_do_not_propagate_without_auditing(tmp_path):
    levels = SmartLogger.levels()

    root = SmartLogger("root.noaudit", level=levels["TRACE"])
    api = SmartLogger("root.noaudit.api", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    root.add_file(log_dir=str(log_dir), logfile_name="root.log")
    api.add_file(log_dir=str(log_dir), logfile_name="api.log")

    api.info("from api")

    root_log = (log_dir / "root.log").read_text(encoding="utf-8")
    api_log = (log_dir / "api.log").read_text(encoding="utf-8")

    assert "from api" not in root_log
    assert "from api" in api_log


def test_retire_and_destroy_logger(tmp_path):
    levels = SmartLogger.levels()
    logger = SmartLogger("lifecycle.test", level=levels["TRACE"])

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add_file(log_dir=str(log_dir), logfile_name="life.log")
    logger.info("before retire")

    logger.retire()
    # after retire, logging should be effectively disabled
    # noinspection PyBroadException
    try:
        logger.info("after retire")
    except Exception:
        ok = True
    else:
        ok = False
    assert ok, "Error! Logging allowed after retire()"

    content = (log_dir / "life.log").read_text(encoding="utf-8")
    assert "before retire" in content
    assert "after retire" not in content

    logger.destroy()
    # recreating with same name should be clean
    logger2 = SmartLogger("lifecycle.test", level=levels["INFO"])
    logger2.add_file(log_dir=str(log_dir), logfile_name="life2.log")
    logger2.info("new logger")

    content2 = (log_dir / "life2.log").read_text(encoding="utf-8")
    assert "new logger" in content2
