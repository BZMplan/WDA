from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Response, status, Query
from fastapi.responses import FileResponse
from services import utils as tools, plot as draw
import config as cfg
import uuid
import json
import time
import pandas as pd
import os
import logging
import asyncio

# 设置路由
router = APIRouter(
    tags=["get"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

# 初始化日志
logger = logging.getLogger("uvicorn.app")


# 弃用，只能选择一个或者全部要素，可用性不高
def _read_station_file(station_name: str, day: str, usecols=None) -> pd.DataFrame:
    path = os.path.join("data", f"{station_name}_{day}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return pd.read_csv(path, sep=",", usecols=usecols)


@router.get("/api/get/info")
async def api_get_info(
    item: cfg.meteorological_elements,
):

    if item.time_local:
        time_local = item.time_local.strftime("%Y-%m-%d %H:%M")
        date = time_local
    else:
        date = pd.to_datetime(datetime.now()).strftime("%Y-%m-%d %H:%M")

    station_name = item.station_name
    time_utc = (pd.to_datetime(date) + timedelta(hours=-8)).strftime("%Y-%m-%d %H:%M")

    plot_elements = draw._select_plot_elements(None)

    selected_cols = [name for name, *_ in plot_elements]

    df = draw._read_station_data(station_name, [date], selected_cols)

    def _native(value):
        if pd.isna(value):
            return None
        return value.item() if hasattr(value, "item") else value

    if df.empty:
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "无数据",
            "data": None,
        }

    result = {
        "station_name": station_name,
        "time_utc": time_utc,
        "time_local": time_local,
    }
    if time_local is None:
        row = df.tail[1].iloc[0]
    else:
        mask = df["time_local"] == time_local
        if mask.any():
            row = df.loc[mask].iloc[-1]
        else:
            return {
                "status": status.HTTP_404_NOT_FOUND,
                "message": "无数据",
                "data": None,
            }

    for col in selected_cols:
        result[col] = _native(row.get(col))

    return {"status": status.HTTP_200_OK, "message": "成功获取数据", "data": result}


# 发送请求获取对应图片的url
@router.get("/api/get/image")
async def api_get_image(
    station_name: str,
    date: str = None,
    elements: str = Query(...),
):
    if date:
        try:
            date = pd.to_datetime(date).strftime("%Y-%m-%d")
        except Exception as e:
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Wrong date: {date}",
            }
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 列参数解析：优先 JSON；失败时支持以逗号分隔
    try:
        element = json.loads(elements)
    except json.JSONDecodeError:
        element = [c.strip() for c in elements.split(",") if c.strip()]

    if len(element) == 1 and element[0] == "all":
        element = cfg.ALLOWED_ELEMENTS

    # 校验列名
    for p in element:
        if p not in cfg.ALLOWED_ELEMENTS:
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": {
                    f"Invalid class: {p}",
                    f"Legal class: {cfg.ALLOWED_ELEMENTS}",
                },
            }

    # 异步绘图，防止阻塞线程
    file_name, image_id = await asyncio.to_thread(
        draw.draw, station_name, date, element
    )

    if not file_name:
        return {"image_id": None, "url": None}

    image_token = str(uuid.uuid4())
    tools.one_time_image_tokens[image_token] = (time.time(), file_name)
    return {
        "image_id": image_id,
        "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
    }


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
