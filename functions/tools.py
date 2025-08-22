from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import logging
import math
import os
import threading
import time


logger = logging.getLogger("uvicorn.app")

class element(BaseModel):
    station_name: Optional[str] = None  # 站点名称
    timestamp: Optional[int] = None  # 时间戳
    temperature: Optional[float] = None  # 气温
    pressure: Optional[float] = None  # 气压
    relative_humidity: Optional[float] = None  # 相对湿度
    wind_speed: Optional[float] = None  # 风速
    wind_direction: Optional[float] = None  # 风向
    ground_temperature: Optional[float] = None  # 地温
    evaporation_capacity: Optional[float] = None  # 蒸发量
    sunshine_duration: Optional[float] = None  # 日照时间

    class Config:
        extra = "ignore"


class data(BaseModel):
    station_name: str
    timestamp: int = None
    element: str = "all"


tokens = ["27ecb87a-1c4c-4b24-940d-2ad04b4dc5a7"]

oauth2_scheme = OAuth2PasswordBearer("")


one_time_image_tokens = {}


def verify(token: str = Depends(oauth2_scheme)):
    if token not in tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired tokens",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def clean_expired_image_tokens():

    while True:
        time.sleep(10)  # 每10秒检查一次
        current_time = time.time()
        # 清理120秒（2分钟）前的令牌
        expired_tokens = [
            t
            for t, (created_time, _) in one_time_image_tokens.items()
            if current_time - created_time > 120
        ]
        for image_token in expired_tokens:
            # 删除token和对应的文件
            _, resource_path = one_time_image_tokens[image_token]
            os.remove(os.path.join("image", resource_path))
            logger.info(f"图片'{os.path.join("image",resource_path)}'过期，已删除")
            del one_time_image_tokens[image_token]


def clean_nan_values(data: dict) -> dict:
    """将字典中的NaN值替换为None,确保JSON序列化正常"""
    return {
        key: None if isinstance(value, float) and math.isnan(value) else value
        for key, value in data.items()
    }


threading.Thread(target=clean_expired_image_tokens, daemon=True).start()
