from fastapi import FastAPI
from routers import get,post
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn


app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)

app.mount("/image", StaticFiles(directory="image"), name="image")

if __name__ == "__main__":

    # 启动服务端

    logger = logging.getLogger("uvicorn.app")

    uvicorn.run(
        app=app, host="0.0.0.0", port=80, workers=1, log_config="./log_config.ini"
    )
