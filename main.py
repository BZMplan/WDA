from fastapi import FastAPI
from routes import get, post
from services import utils as tools, bootstrap as init
import uvicorn
import threading
import logging

logger = logging.getLogger("uvicorn.app")
app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)

# 暂时停工
# app.include_router(main_page.router)
# app.mount("/static", StaticFiles(directory="static"), name="static")

threading.Thread(target=tools.clean_expired_image_tokens, daemon=True).start()

if __name__ == "__main__":

    # 初始化文件夹
    init.setup_dirs()
    init.setup_dirs(base="data", names=["sensorlog"])
    
    # 初始化数据库
    init.init_postgresql()
    
    # 初始化配置文件
    log_config_path = init.setup_log_config()

    uvicorn.run(
        app=app, host="0.0.0.0", port=7763, workers=1, log_config=log_config_path
    )
