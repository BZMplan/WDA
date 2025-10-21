from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, status, Query
from fastapi.responses import FileResponse
from typing import List, Union
from services import utils as tools, plot as draw
import uuid
import json
import time
import pandas as pd
import os
import logging
import asyncio

# 常量：允许的气象元素
ALLOWED_CLASSES: List[str] = [
    "temperature",
    "pressure",
    "relative_humidity",
    "wind_speed",
    "wind_direction",
    "ground_temperature",
    "evaporation_capacity",
    "sunshine_duration",
]

# 设置路由
router = APIRouter(
    tags=["get"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

# 初始化日志
logger = logging.getLogger("uvicorn.app")


def _read_station_file(station_name: str, day: str, usecols=None) -> pd.DataFrame:
    path = os.path.join("data", f"{station_name}_{day}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep="|", usecols=usecols)


@router.get("/api/get")
async def api_get(
    station_name: str, timestamp: int | None = None, element: str = "all"
):
    day = (
        time.strftime("%Y-%m-%d", time.localtime(timestamp))
        if timestamp
        else time.strftime("%Y-%m-%d", time.localtime(int(time.time())))
    )

    try:
        # 只读取必要列以提速
        if element == "all":
            df = _read_station_file(station_name, day)
        else:
            df = _read_station_file(
                station_name, day, usecols=["station_name", "timestamp", element]
            )
    except FileNotFoundError:
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "data file not found",
            "data": None,
        }
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"read csv failed: {e}",
            "data": None,
        }

    if df.empty:
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "no data found",
            "data": None,
        }

    # 元素校验（仅当不是 all 时）
    if element != "all" and element not in df.columns:
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "element not found",
            "data": None,
        }

    if timestamp is None:
        row = df.tail(1)
        if element == "all":
            result = row.to_dict(orient="records")[0]
        else:
            result = row[["station_name", "timestamp", element]].to_dict(
                orient="records"
            )[0]
    else:
        mask = df["timestamp"] == timestamp
        if not mask.any():
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "message": "no data at the given timestamp",
                "data": None,
            }
        sub = df.loc[mask]
        if element == "all":
            result = sub.to_dict(orient="records")[0]
        else:
            result = sub[["station_name", "timestamp", element]].to_dict(
                orient="records"
            )[0]

    result = tools.clean_nan_values(result)
    return {"status": status.HTTP_200_OK, "message": "query success", "data": result}


# 发送请求获取对应图片的url
@router.get("/api/get/image")
async def api_get_image(
    mode: str,
    station_name: str,
    param: Union[int, str],
    columns: str = Query(...),
):

    # 列参数解析：优先 JSON；失败时支持以逗号分隔
    try:
        column = json.loads(columns)
    except json.JSONDecodeError:
        column = [c.strip() for c in columns.split(",") if c.strip()]

    # 校验列名
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

        # 异步绘图，防止阻塞线程
        file_name, info, image_id = await asyncio.to_thread(
            draw.draw_specific_day_pro,
            station_name,
            column,
            param,
            sep="|",
            zone="Asia/Shanghai",
        )

        image_token = str(uuid.uuid4())
        tools.one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
            "image_id": image_id,
            "info": info,
        }
    elif mode == "hour":
        param = int(param) if not isinstance(param, int) else param

        # 异步绘图，防止阻塞线程
        file_name, info, image_id = await asyncio.to_thread(
            draw.draw_last_hour_pro,
            station_name,
            column,
            param,
            sep="|",
            zone="Asia/Shanghai",
        )

        image_token = str(uuid.uuid4())
        tools.one_time_image_tokens[image_token] = (time.time(), file_name)
        return {
            "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
            "image_id": image_id,
            "info": info,
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

    created_time, file_name = tools.one_time_image_tokens.get(image_token)
    if time.time() - created_time > 120:
        # 过期直接移除
        tools.one_time_image_tokens.pop(image_token, None)
        raise HTTPException(status_code=403, detail="URL已过期")

    # 一次性 token：消费后移除，文件由清理线程回收
    tools.one_time_image_tokens.pop(image_token, None)
    return FileResponse(os.path.join("images", file_name))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # return FileResponse(os.path.join("static", "favicon.ico"))
    return Response(status_code=204)
