from fastapi import FastAPI
from routers import get,post,oauth
from functions import tools
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn
import threading



app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)
app.include_router(oauth.router)

app.mount("/image", StaticFiles(directory="image"), name="image")
threading.Thread(target=tools.clean_expired_image_tokens, daemon=True).start()

if __name__ == "__main__":

    # 启动服务端

    logger = logging.getLogger("uvicorn.app")

    uvicorn.run(
        app=app, host="0.0.0.0", port=80, workers=1, log_config="./log_config.ini"
    )
