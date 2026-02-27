import logging
import logging.config
import threading

import uvicorn
import yaml
from fastapi import FastAPI

from app.api.v1 import get as get_v1
from app.api.v1 import post as post_v1
from app.api.v2 import post as post_v2
from app.core import bootstrap, config
from app.services import weather

logger = logging.getLogger("uvicorn.app")


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(post_v1.router)
    app.include_router(get_v1.router)
    app.include_router(post_v2.router)
    return app


app = create_app()


def run() -> None:
    logging_config = config.load_logging_config()
    with open(logging_config, "r", encoding="utf-8") as f:
        logging.config.dictConfig(yaml.safe_load(f))

    bootstrap.init_dirs()
    bootstrap.init_dirs(base="data", names=["sensorlog"])
    bootstrap.init_postgresql()

    threading.Thread(target=weather.clean_expired_image_tokens, daemon=True).start()

    uvicorn.run(
        app=app,
        host="0.0.0.0",
        port=7763,
        workers=1,
        log_config=logging_config,
    )
