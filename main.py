import threading, logging

import uvicorn
from fastapi import FastAPI

from routes import get, post
from services import init
from services import config
from services import utils

logger = logging.getLogger("uvicorn.app")

app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)

threading.Thread(target=utils.clean_expired_image_tokens, daemon=True).start()

if __name__ == "__main__":
    # 初始化文件夹
    init.init_dirs()
    init.init_dirs(base="data", names=["sensorlog"])

    # 初始化数据库
    init.init_postgresql()

    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=7763,
        workers=1,
        log_config=config.load_logging_config(),
    )
