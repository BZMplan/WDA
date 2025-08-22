from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.params import Query
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pandas.io.common import file_exists
from pydantic import BaseModel
from typing import Optional, Union
import os
import pandas as pd
import time
import math
import threading
import uuid
import draw
import logging
import uvicorn
import json

app = FastAPI()

app.mount("/image", StaticFiles(directory="image"), name="image")


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


# 上传站点数据，需要token验证
@app.post("/api/upload/official")
async def api_upload_official(item: element, token: str = Depends(verify)):
    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())
    temperature = item.temperature if item.temperature is not None else "NULL"
    pressure = item.pressure if item.pressure is not None else "NULL"
    relative_humidity = (
        item.relative_humidity if item.relative_humidity is not None else "NULL"
    )
    wind_speed = item.wind_speed if item.wind_speed is not None else "NULL"
    wind_direction = item.wind_direction if item.wind_direction is not None else "NULL"
    ground_temperature = (
        item.ground_temperature if item.ground_temperature is not None else "NULL"
    )
    evaporation_capacity = (
        item.evaporation_capacity if item.evaporation_capacity is not None else "NULL"
    )
    sunshine_duration = (
        item.sunshine_duration if item.sunshine_duration is not None else "NULL"
    )

    today = time.strftime("%Y-%m-%d", time.localtime(timestamp))

    data = {
        "station_name": station_name,
        "timestamp": timestamp,
        "temperature": temperature,
        "pressure": pressure,
        "relative_humidity": relative_humidity,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "ground_temperature": ground_temperature,
        "evaporation_capacity": evaporation_capacity,
        "sunshine_duration": sunshine_duration,
    }

    df = pd.DataFrame(data, index=[0])
    file_name = f"{station_name}_{today}.csv"
    df.to_csv(
        f"./data/official/{file_name}",
        index=False,
        header=not file_exists(f"./data/official/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": data}


# 上传站点数据到test，不需要token验证
@app.post("/api/upload/test")
async def api_upload_test(item: element):
    # 获取当前日期

    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())
    temperature = item.temperature if item.temperature is not None else "NULL"
    pressure = item.pressure if item.pressure is not None else "NULL"
    relative_humidity = (
        item.relative_humidity if item.relative_humidity is not None else "NULL"
    )
    wind_speed = item.wind_speed if item.wind_speed is not None else "NULL"
    wind_direction = item.wind_direction if item.wind_direction is not None else "NULL"
    ground_temperature = (
        item.ground_temperature if item.ground_temperature is not None else "NULL"
    )
    evaporation_capacity = (
        item.evaporation_capacity if item.evaporation_capacity is not None else "NULL"
    )
    sunshine_duration = (
        item.sunshine_duration if item.sunshine_duration is not None else "NULL"
    )

    today = time.strftime("%Y-%m-%d", time.localtime(timestamp))

    data = {
        "station_name": station_name,
        "timestamp": timestamp,
        "temperature": temperature,
        "pressure": pressure,
        "relative_humidity": relative_humidity,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "ground_temperature": ground_temperature,
        "evaporation_capacity": evaporation_capacity,
        "sunshine_duration": sunshine_duration,
    }

    df = pd.DataFrame(data, index=[0])
    file_name = f"{station_name}_{today}.csv"
    df.to_csv(
        f"./data/test/{file_name}",
        index=False,
        header=not file_exists(f"./data/test/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": data}


# 获取站点数据，需要token验证
@app.get("/api/get/official")
async def api_get_official(
    station_name: str,
    timestamp: int = None,
    element: str = "all",
    token: str = Depends(verify),
):
    # 未指定时间戳时，返回最新数据
    if timestamp is None:
        file_name = f"{station_name}.csv"
        df = pd.read_csv(f"./data/official/{file_name}", sep="|")

        if element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].to_dict(
                orient="records"
            )[-1]
        else:
            if element not in df.columns:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "element not found",
                    "data": None,
                }
            result = df[["station_name", "timestamp", element]].to_dict(
                orient="records"
            )[-1]
            if not result:
                return {
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "no data found",
                    "data": None,
                }

        result = clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }
    # 指定时间戳时，返回该时间戳的数据
    else:
        file_name = f"{station_name}.csv"
        df = pd.read_csv(f"./data/official/{file_name}", sep="|")

        if element == "all":
            result = (
                df[["station_name", "timestamp"] + list(df.columns[2:])]
                .loc[df["timestamp"] == timestamp]
                .to_dict(orient="records")[-1]
            )
        else:
            if element not in df.columns:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "element not found",
                    "data": None,
                }
            result = (
                df[["station_name", "timestamp", element]]
                .loc[df["timestamp"] == timestamp]
                .to_dict(orient="records")[-1]
            )
            if not result:
                return {
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "no data found",
                    "data": None,
                }

        result = clean_nan_values(result)

        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }


# 获取站点数据从test，不需要token验证
@app.get("/api/get/test")
async def api_get_test(station_name: str, timestamp: int = None, element: str = "all"):

    # 未指定时间戳时，返回最新数据
    if timestamp is None:
        file_name = f"{station_name}.csv"
        df = pd.read_csv(f"./data/test/{file_name}", sep="|")

        if element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].to_dict(
                orient="records"
            )[-1]
        else:
            if element not in df.columns:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "element not found",
                    "data": None,
                }
            result = df[["station_name", "timestamp", element]].to_dict(
                orient="records"
            )[-1]
            if not result:
                return {
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "no data found",
                    "data": None,
                }

        result = clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }
    # 指定时间戳时，返回该时间戳的数据
    else:
        file_name = f"{station_name}.csv"
        df = pd.read_csv(f"./data/test/{file_name}", sep="|")

        if element == "all":
            result = (
                df[["station_name", "timestamp"] + list(df.columns[2:])]
                .loc[df["timestamp"] == timestamp]
                .to_dict(orient="records")[-1]
            )
        else:
            if element not in df.columns:
                return {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "element not found",
                    "data": None,
                }
            result = (
                df[["station_name", "timestamp", element]]
                .loc[df["timestamp"] == timestamp]
                .to_dict(orient="records")[-1]
            )
            if not result:
                return {
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "no data found",
                    "data": None,
                }

        result = clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }


# 发送请求获取对应图片的url
@app.get("/api/get/image")
async def api_get_image(
    mode: str,
    database: str,
    station_name: str,
    param: Union[int, str],
    columns: str = Query(...),
):

    ALLOWED_CLASSES = [
        "temperature",
        "pressure",
        "relative_humidity",
        "wind_speed",
        "wind_direction",
        "ground_temperature",
        "evaporation_capacity",
        "sunshine_duration",
    ]

    try:
        column = json.loads(columns)
    except json.JSONDecodeError:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": {f"Invalid colums: {columns}", "Legal colums: ['xxx','xxx']"},
        }

    # 判断cls的数据是否合法，若不合法则返回错误信息
    for c in column:
        if c not in ALLOWED_CLASSES:
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": {f"Invalid class: {c}", f"Legal class: {ALLOWED_CLASSES}"},
            }

    if mode == "date":
        # 处理日期参数，确保是字符串格式的日期
        param = (
            datetime.strptime(param, "%Y-%m-%d") if isinstance(param, str) else param
        ).strftime("%Y-%m-%d")

        file_name, info = draw.draw_specific_day_pro(
            database, station_name, column, param, sep="|", zone="Asia/Shanghai"
        )
        image_token = str(uuid.uuid4())
        one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1/image?image_token={image_token}",
            "info": info,
        }
    elif mode == "hour":
        param = int(param) if not isinstance(param, int) else param

        file_name, info = draw.draw_last_hour_pro(
            database, station_name, column, param, sep="|", zone="Asia/Shanghai"
        )
        image_token = str(uuid.uuid4())
        one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1/image?image_token={image_token}",
            "info": info,
        }
    else:
        logger.error(f"Wrong Mode: {mode}, need 'date' or 'hour'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong Mode: {mode}, need 'date' or 'hour'",
        )


# 显示图片资源
@app.get("/image")
async def image(image_token: str):
    if image_token not in one_time_image_tokens:
        raise HTTPException(status_code=403, detail="URL无效或已被使用")

    created_time, file_name = one_time_image_tokens[image_token]

    if time.time() - created_time > 120:
        raise HTTPException(status_code=403, detail="URL已过期")

    # 返回静态资源
    return FileResponse(os.path.join("image", file_name))


if __name__ == "__main__":

    # 启动服务端

    logger = logging.getLogger("uvicorn.app")

    uvicorn.run(
        app=app, host="0.0.0.0", port=80, workers=1, log_config="./log_config.ini"
    )
