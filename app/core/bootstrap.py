import logging
from pathlib import Path

from app.db.sql import create_image_tokons_table

logger = logging.getLogger("uvicorn.app")


def init_dirs(base=".", names=("data", "images", "logs")):
    """
    初始化运行所需的外部文件夹。

    默认在当前工作目录创建 data/images/logs
    允许通过 base/names 定制，保持向后兼容

    参数:
        base (str): 基础路径，默认为当前目录
        names (Iterable[str]): 文件夹名称列表
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
    logger.info("数据库初始化成功")
