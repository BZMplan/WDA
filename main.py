from pathlib import Path
from fastapi import FastAPI
from routers import get,post,oauth,home_page
from functions import tools,init
from fastapi.staticfiles import StaticFiles
import uvicorn
import threading

app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)
app.include_router(oauth.router)
app.include_router(home_page.router)

app.mount("/static",StaticFiles(directory="static"),name="static")

threading.Thread(target=tools.clean_expired_image_tokens, daemon=True).start()


if __name__ == "__main__":
    
    # 初始化文件夹
    init.setup_dirs()
    
    # 初始化配置文件
    log_config_path = init.setup_log_config()
    
    uvicorn.run(
        app=app, host="0.0.0.0", port=81, workers=1, log_config=log_config_path
    )
