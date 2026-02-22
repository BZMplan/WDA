import atexit
import logging
import os
from pathlib import Path
import sys
import tempfile

import yaml

logger = logging.getLogger("uvicorn.app")


def _find_log_config_path():
    """
    在常见位置查找 log_config.yaml。找不到则返回 None。

    返回:
        Optional[Path]: 配置文件路径或 None
    """
    candidates = [
        Path.cwd() / "log_config.yaml",
        Path(__file__).resolve().parent.parent / "log_config.yaml",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def _write_temp_config(content):
    """
    将配置写入临时 .yaml 文件并注册退出清理，返回文件路径。

    参数:
        content (str): 配置内容

    返回:
        str: 临时文件路径
    """
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(content)
        tmp.flush()
    finally:
        tmp.close()
    atexit.register(lambda p=tmp.name: os.path.exists(p) and os.remove(p))
    return tmp.name


def load_logging_config():
    """
    返回可供 uvicorn 使用的日志配置文件路径。

    - 打包环境（sys.frozen）：从临时目录读取原始配置并复制到可写的临时文件
    - 开发环境：优先使用当前工作目录/项目根的 log_config.yaml
    - 若找不到配置文件，则生成最小可用的日志配置到临时文件并返回

    返回:
        str: 日志配置文件路径
    """
    minimal_config = """
version: 1
disable_existing_loggers: false
formatters:
  default:
    format: "%(asctime)s [%(process)d] - %(levelname)s [%(thread)d] - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
loggers:
  root:
    level: INFO
    handlers: [console]
  uvicorn:
    level: INFO
    handlers: [console]
    qualname: uvicorn
    propagate: false
""".strip()

    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        packaged = base_dir / "log_config.yaml"
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

    logger.warning("未找到日志配置文件log_config.yaml，使用最小配置")
    return _write_temp_config(minimal_config)


def load_postgresql_config(path="./sql_config.yaml"):
    """
    初始化数据库配置

    从 YAML 配置文件加载配置信息到全局 CONFIG 变量。

    参数:
        path (str): 配置文件路径，默认为 "./sql_config.yaml"
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            SQL_CONFIG = yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"错误：找不到配置文件 {path},使用空配置")
        SQL_CONFIG = {}
    except yaml.YAMLError as e:
        logger.warning(f"错误：解析 YAML 出错: {e}")
        SQL_CONFIG = {}

    return SQL_CONFIG


def load_plot_config(path="./plot_config.yaml"):
    """
    初始化数据库配置

    从 YAML 配置文件加载配置信息到全局 CONFIG 变量。

    参数:
        path (str): 配置文件路径，默认为 "./plot_config.yaml"
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            PLOT_CONFIG = yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"错误：找不到配置文件 {path},使用空配置")
        PLOT_CONFIG = {}
    except yaml.YAMLError as e:
        logger.warning(f"错误：解析 YAML 出错: {e}")
        PLOT_CONFIG = {}

    return PLOT_CONFIG
