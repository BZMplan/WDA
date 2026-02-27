import atexit
import logging
import os
from pathlib import Path
import sys
import tempfile

import yaml

logger = logging.getLogger("uvicorn.app")


def _find_file(file_name: str):
    candidates = [
        Path.cwd() / file_name,
        Path(__file__).resolve().parent.parent / file_name,
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


def _read_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_app_config(path="./config.yaml"):
    """
    读取统一配置文件，找不到时返回空配置。
    """
    cfg_path = _find_file(path) if path == "./config.yaml" else Path(path)
    if cfg_path is None:
        logger.warning("未找到配置文件 config.yaml，使用空配置")
        return {}

    try:
        return _read_yaml(cfg_path)
    except yaml.YAMLError as e:
        logger.warning("解析配置文件失败: %s", e)
        return {}
    except OSError as e:
        logger.warning("读取配置文件失败: %s", e)
        return {}


def load_logging_config():
    """
    返回可供 uvicorn 使用的日志配置文件路径。

    - 打包环境（sys.frozen）：从临时目录读取原始配置并复制到可写的临时文件
    - 优先从统一 config.yaml 的 logging 段读取
    - 兼容旧版 log_config.yaml
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
        packaged = base_dir / "config.yaml"
        try:
            if packaged.is_file():
                app_cfg = _read_yaml(packaged)
                logging_cfg = app_cfg.get("logging")
                if logging_cfg:
                    return _write_temp_config(
                        yaml.safe_dump(logging_cfg, allow_unicode=True, sort_keys=False)
                    )
                logger.warning("打包配置缺少 logging 段，使用最小配置")
                return _write_temp_config(minimal_config)
            else:
                logger.warning("未找到打包配置文件 config.yaml，使用最小配置")
                return _write_temp_config(minimal_config)
        except Exception as e:
            logger.warning("读取打包日志配置失败: %s，使用最小配置", e)
            return _write_temp_config(minimal_config)

    app_cfg = load_app_config()
    logging_cfg = app_cfg.get("logging")
    if logging_cfg:
        return _write_temp_config(
            yaml.safe_dump(logging_cfg, allow_unicode=True, sort_keys=False)
        )

    legacy_cfg = _find_file("log_config.yaml")
    if legacy_cfg is not None:
        return str(legacy_cfg)

    logger.warning("未找到日志配置，使用最小配置")
    return _write_temp_config(minimal_config)


def load_postgresql_config(path="./config.yaml"):
    """
    初始化数据库配置（统一配置）。

    参数:
        path (str): 配置文件路径，默认为 "./config.yaml"
    """
    if path == "./config.yaml":
        app_cfg = load_app_config(path)
        if app_cfg:
            return app_cfg
        legacy_cfg = _find_file("sql_config.yaml")
        if legacy_cfg:
            try:
                return _read_yaml(legacy_cfg)
            except (yaml.YAMLError, OSError) as e:
                logger.warning("读取旧配置 sql_config.yaml 失败: %s", e)
        return {}

    try:
        return _read_yaml(Path(path))
    except FileNotFoundError:
        logger.warning("错误：找不到配置文件 %s, 使用空配置", path)
        return {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("错误：解析 YAML 出错: %s", e)
        return {}


def load_plot_config(path="./config.yaml"):
    """
    初始化绘图配置（统一配置）。

    参数:
        path (str): 配置文件路径，默认为 "./config.yaml"
    """
    if path == "./config.yaml":
        app_cfg = load_app_config(path)
        plot_cfg = app_cfg.get("plot")
        if isinstance(plot_cfg, dict):
            return plot_cfg
        legacy_cfg = _find_file("plot_config.yaml")
        if legacy_cfg:
            try:
                return _read_yaml(legacy_cfg)
            except (yaml.YAMLError, OSError) as e:
                logger.warning("读取旧配置 plot_config.yaml 失败: %s", e)
        return {}

    try:
        return _read_yaml(Path(path))
    except FileNotFoundError:
        logger.warning("错误：找不到配置文件 %s, 使用空配置", path)
        return {}
    except (yaml.YAMLError, OSError) as e:
        logger.warning("错误：解析 YAML 出错: %s", e)
        return {}
