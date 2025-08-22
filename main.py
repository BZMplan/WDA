from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
import pandas as pd
import time
import math
import threading
import logging
import uvicorn
from routers import get,post

app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)

app.mount("/image", StaticFiles(directory="image"), name="image")

if __name__ == "__main__":

    # 启动服务端

    logger = logging.getLogger("uvicorn.app")

    uvicorn.run(
        app=app, host="0.0.0.0", port=81, workers=1, log_config="./log_config.ini"
    )
