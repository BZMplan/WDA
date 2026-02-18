import atexit
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from services.postgresql import create_image_tokons_table

logger = logging.getLogger("uvicorn.app")


def setup_dirs(base=".", names=("data", "images", "logs")):
    """
    初始化运行所需的外部文件夹。

    - 默认在当前工作目录创建 data/images/logs
    - 允许通过 base/names 定制，保持向后兼容
    """
    base_path = Path(base)
    created = []
    for name in names:
        path = base_path / name
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    logger.info("初始化文件夹成功: %s", ", ".join(created))


def init_postgresql():
    """初始化数据库"""
    create_image_tokons_table("image_tokens")


def _find_log_config_path():
    """在常见位置查找 log_config.ini。找不到则返回 None。"""
    candidates = [
        Path.cwd() / "log_config.ini",
        Path(__file__).resolve().parent.parent / "log_config.ini",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _write_temp_config(content):
    """将配置写入临时 .ini 文件并注册退出清理，返回文件路径。"""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".ini", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(content)
        tmp.flush()
    finally:
        tmp.close()
    atexit.register(lambda p=tmp.name: os.path.exists(p) and os.remove(p))
    return tmp.name


def setup_log_config():
    """
    返回可供 uvicorn 使用的日志配置文件路径。

    - 打包环境（sys.frozen）：从临时目录读取原始配置并复制到可写的临时文件
    - 开发环境：优先使用当前工作目录/项目根的 log_config.ini
    - 若找不到配置文件，则生成最小可用的日志配置到临时文件并返回
    """
    minimal_config = """
[loggers]
keys=root,uvicorn

[handlers]
keys=console

[formatters]
keys=default

[logger_root]
level=INFO
handlers=console

[logger_uvicorn]
level=INFO
handlers=console
qualname=uvicorn
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=default
args=(sys.stdout,)

[formatter_default]
format=%(asctime)s [%(process)d] - %(levelname)s [%(thread)d] - %(message)s
datefmt=%Y-%m-%d %H:%M:%S,%f
""".strip()

    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        packaged = base_dir / "log_config.ini"
        try:
            if packaged.is_file():
                content = packaged.read_text(encoding="utf-8")
                return _write_temp_config(content)
            else:
                logger.warning("未找到打包内日志配置，使用最小配置")
                return _write_temp_config(minimal_config)
        except Exception as e:
            logger.warning("读取打包日志配置失败: %s，使用最小配置", e)
            return _write_temp_config(minimal_config)

    cfg = _find_log_config_path()
    if cfg is not None:
        return str(cfg)

    logger.warning("未找到日志配置文件log_config.ini，使用最小配置")
    return _write_temp_config(minimal_config)
