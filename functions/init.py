from pathlib import Path
import os
import sys
import tempfile
import logging

logger = logging.getLogger("uvicorn.app")


# 初始化所需要的外部文件夹
def setup_dirs():
    # data
    os.makedirs("data", exist_ok=True)

    # image
    os.makedirs("image", exist_ok=True)

    # logs
    os.makedirs("logs", exist_ok=True)

    logger.info("初始化文件夹成功")


# 读取内置的日志配置文件
def setup_log_config():
    """设置日志配置文件"""
    if getattr(sys, "frozen", False):
        # 打包环境：从临时目录读取配置文件
        base_dir = Path(sys._MEIPASS)
        original_config_path = base_dir / "log_config.ini"

        # 将配置文件复制到临时文件（因为uvicorn可能需要写入权限）
        with open(original_config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        # 创建临时文件
        temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False)
        temp_config.write(config_content)
        temp_config.close()

        return temp_config.name
    else:
        # 开发环境：使用原始文件
        return "./log_config.ini"
