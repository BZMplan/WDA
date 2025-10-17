from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from typing import Union
from functions import tools,draw
import uuid
import json
import time
import pandas as pd
import os
import routers.oauth
import logging

# 设置路由
router = APIRouter(
    tags=["get"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

# 初始化日志
logger = logging.getLogger("uvicorn.app")

# 获取站点数据，需要token验证
@router.get("/api/get/official")
async def api_get_official(
    station_name: str,
    timestamp: int = None,
    element: str = "all",
    token: str = Depends(routers.oauth.verify_user_status),
):
    
    day = time.strftime("%Y-%m-%d", time.localtime(timestamp)) if timestamp else time.strftime("%Y-%m-%d", time.localtime(int(time.time())))
    file_name = f"{station_name}_{day}.csv"
    
    # 未指定时间戳时，返回最新数据
    if timestamp is None:
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

        result = tools.clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }
    # 指定时间戳时，返回该时间戳的数据
    else:
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

        result = tools.clean_nan_values(result)

        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }


# 获取站点数据从test，不需要token验证
@router.get("/api/get/test")
async def api_get_test(station_name: str, timestamp: int = None, element: str = "all"):

    day = time.strftime("%Y-%m-%d", time.localtime(timestamp)) if timestamp else time.strftime("%Y-%m-%d", time.localtime(int(time.time())))
    file_name = f"{station_name}_{day}.csv"

    # 未指定时间戳时，返回最新数据
    if timestamp is None:
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

        result = tools.clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }
    # 指定时间戳时，返回该时间戳的数据
    else:
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

        result = tools.clean_nan_values(result)
        return {
            "status": status.HTTP_200_OK,
            "message": "query success",
            "data": result,
        }


# 发送请求获取对应图片的url
@router.get("/api/get/image")
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

        file_name, info, image_id = draw.draw_specific_day_pro(
            database, station_name, column, param, sep="|", zone="Asia/Shanghai"
        )
        image_token = str(uuid.uuid4())
        tools.one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
            "image_id":image_id,
            "info": info
        }
    elif mode == "hour":
        param = int(param) if not isinstance(param, int) else param

        file_name, info, image_id = draw.draw_last_hour_pro(
            database, station_name, column, param, sep="|", zone="Asia/Shanghai"
        )
        image_token = str(uuid.uuid4())
        tools.one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
            "image_id":image_id,
            "info": info
        }
    else:
        logger.error(f"Wrong Mode: {mode}, need 'date' or 'hour'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Wrong Mode: {mode}, need 'date' or 'hour'",
        )


# 显示图片资源
@router.get("/image")
async def image(image_token: str):
    if image_token not in tools.one_time_image_tokens:
        raise HTTPException(status_code=403, detail="URL无效或已被使用")

    created_time, file_name = tools.one_time_image_tokens[image_token]

    if time.time() - created_time > 120:
        raise HTTPException(status_code=403, detail="URL已过期")

    # 返回静态资源
    return FileResponse(os.path.join("image", file_name))
