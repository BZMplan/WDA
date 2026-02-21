import logging
import logging.config
import threading

import uvicorn
import yaml
from fastapi import FastAPI

from routes import get, post
from services import init
from services import config
from services import utils

logger = logging.getLogger("uvicorn.app")


app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)


if __name__ == "__main__":
    # 初始化日志
    logging_config = config.load_logging_config()
    with open(logging_config, "r", encoding="utf-8") as f:
        logging.config.dictConfig(yaml.safe_load(f))

    # 初始化文件夹
    init.init_dirs()
    init.init_dirs(base="data", names=["sensorlog"])

    # 初始化数据库
    init.init_postgresql()

    # 启动后台进程
    threading.Thread(target=utils.clean_expired_image_tokens, daemon=True).start()

    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=7763,
        workers=1,
        log_config=logging_config,
    )
