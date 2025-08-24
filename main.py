from pathlib import Path
from fastapi import FastAPI
from routers import get,post,oauth
from functions import tools,init
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn
import threading

app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)
app.include_router(oauth.router)


threading.Thread(target=tools.clean_expired_image_tokens, daemon=True).start()


if __name__ == "__main__":
    
    # 初始化文件夹
    init.setup_dirs()
    
    # 初始化配置文件
    log_config_path = init.setup_log_config()
    
    # 启动服务端
    app.mount("/image", StaticFiles(directory="image"), name="image")
    uvicorn.run(
        app=app, host="0.0.0.0", port=80, workers=1, log_config=log_config_path
    )
