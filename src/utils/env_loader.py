from __future__ import annotations

from pathlib import Path

from utils.logger import logger

_loaded = False


def load_env() -> bool:
    global _loaded
    if _loaded:
        return True
    _loaded = True

    try:
        from dotenv import load_dotenv
    except Exception:
        return False

    env_path = Path(".env")
    if not env_path.exists():
        return False

    ok = load_dotenv(dotenv_path=env_path, override=False)
    if ok:
        logger.info("已加载 .env 配置")
    return bool(ok)

