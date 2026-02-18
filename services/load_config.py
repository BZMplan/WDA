import logging

import yaml

logger = logging.getLogger("uvicorn.app")
CONFIG = {}


def load_postgresql(path="./config.yaml"):
    """
    初始化数据库配置

    从 YAML 配置文件加载配置信息到全局 CONFIG 变量。

    参数:
        path (str): 配置文件路径，默认为 "./config.yaml"
    """
    global CONFIG
    try:
        with open(path, "r", encoding="utf-8") as file:
            CONFIG = yaml.safe_load(file)
    except FileNotFoundError:
        logger.warning(f"错误：找不到配置文件 {path},使用空配置")
        CONFIG = {}
    except yaml.YAMLError as e:
        logger.warning(f"错误：解析 YAML 出错: {e}")
        CONFIG = {}


load_postgresql()
