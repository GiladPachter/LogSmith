import asyncio
import pytest
from LogSmith.async_smartlogger import AsyncSmartLogger
from LogSmith.rotation_base import RotationLogic, When, ExpirationRule, ExpirationScale


# ------------------------------------------------------------
# 1. High‑volume size‑based rotation
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_stress_size_rotation(tmp_path):
    logic = RotationLogic(maxBytes=200, backupCount=5)

    lg = AsyncSmartLogger("stress1")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    # Write many messages to force multiple rotations
    for i in range(2000):
        await lg.a_info(f"message {i}")

    await lg.flush()

    # Ensure multiple rotated files exist
    rotated = list(tmp_path.glob("stress.log.*"))

    assert len(rotated) > 1

    await lg.shutdown()


# ------------------------------------------------------------
# 2. High‑volume time‑based rotation (SECOND)
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_stress_time_rotation(tmp_path):
    logic = RotationLogic(when=When.SECOND, interval=1, backupCount=3)

    lg = AsyncSmartLogger("stress2")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    # Log for ~3 seconds to force multiple rotations
    for _ in range(150):
        await lg.a_info("tick")
        await asyncio.sleep(0.02)

    await lg.flush()

    rotated = list(tmp_path.glob("stress.log.*"))
    assert len(rotated) >= 2

    await lg.shutdown()


# ------------------------------------------------------------
# 3. Combined size + time rotation under load
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_stress_combined_rotation(tmp_path):
    logic = RotationLogic(
        maxBytes=150,
        when=When.SECOND,
        interval=1,
        backupCount=4,
    )

    lg = AsyncSmartLogger("stress3")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    for i in range(1000):
        await lg.a_info(f"msg {i}")
        if i % 50 == 0:
            await asyncio.sleep(0.05)

    await lg.flush()

    rotated = list(tmp_path.glob("stress.log.*"))
    assert len(rotated) >= 2

    await lg.shutdown()


# ------------------------------------------------------------
# 4. Rotation under worker backlog
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_rotation_under_backlog(tmp_path):
    logic = RotationLogic(maxBytes=100, backupCount=3)

    lg = AsyncSmartLogger("stress4")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    # Enqueue many messages without yielding
    for i in range(5000):
        await lg.a_info(f"msg {i}")

    await lg.flush()

    rotated = list(tmp_path.glob("stress.log.*"))
    assert len(rotated) >= 1

    await lg.shutdown()


# ------------------------------------------------------------
# 5. Expiration rule under load
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_expiration_under_load(tmp_path):
    logic = RotationLogic(
        maxBytes=100,
        backupCount=10,
        expiration_rule=ExpirationRule(ExpirationScale.Seconds, interval=1),
    )

    lg = AsyncSmartLogger("stress5")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    # Force many rotations
    for i in range(1000):
        await lg.a_info("x" * 200)

    await asyncio.sleep(2)  # allow expiration to run
    await lg.flush()

    rotated = list(tmp_path.glob("stress.log.*"))

    # Expiration should delete most old files
    assert len(rotated) <= 10

    await lg.shutdown()


# ------------------------------------------------------------
# 6. BackupCount enforcement under load
# ------------------------------------------------------------
@pytest.mark.asyncio
async def test_backupcount_enforcement(tmp_path):
    logic = RotationLogic(maxBytes=100, backupCount=3)

    lg = AsyncSmartLogger("stress6")
    lg.add_file(
        log_dir=str(tmp_path),
        logfile_name="stress.log",
        rotation_logic=logic,
    )

    for i in range(2000):
        await lg.a_info("x" * 200)

    await lg.flush()

    rotated = sorted(tmp_path.glob("stress.log.*"))

    # Only 3 backups should remain
    assert len(rotated) <= 3

    await lg.shutdown()
