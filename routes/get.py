import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import FileResponse

import services.config as cfg
from services import plot, postgresql

router = APIRouter(tags=["get"])

logger = logging.getLogger("uvicorn.app")


@router.get("/api/get/info")
async def api_get_info(
    station_name: str = None,
) -> Dict[str, Any]:
    """
    获取实时站点数据

    参数:
        station_name: 站点名称 (str, optional)

    返回:
        Dict[str, Any]: 包含状态码、消息和数据的字典
    """
    timestamp = int(time.time())
    day = time.strftime("%Y_%m_%d", time.localtime(timestamp))
    table_name = f"table_{station_name}_{day}"

    if not postgresql.table_exists(table_name):
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "无数据",
            "data": None,
        }

    data = postgresql.get_latest_data(table_name)
    if data is not None and isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")

    logger.info("数据查询成功")
    return {"status": status.HTTP_200_OK, "message": "成功获取数据", "data": data}


@router.get("/api/get/image")
async def api_get_image(
    station_name: str,
    date: str = None,
    elements: str = Query(...),
) -> Dict[str, Any]:
    """
    发送请求获取对应图片的url

    参数:
        station_name: 站点名称 (str)
        date: 日期，格式为YYYY_MM_DD，默认为当天 (str, optional)
        elements: 要绘制的要素列表，支持JSON数组或逗号分隔字符串 (str)

    返回:
        Dict[str, Any]: 包含状态码、图片ID和访问URL的字典
    """
    if not date:
        date = datetime.now().strftime("%Y_%m_%d")

    try:
        date = pd.to_datetime(date, format="%Y_%m_%d").strftime("%Y_%m_%d")
    except (ValueError, TypeError):
        return {
            "status": status.HTTP_400_BAD_REQUEST,
            "message": f"Wrong date: {date}",
        }

    # 列参数解析：优先 JSON；失败时支持以逗号分隔
    try:
        element = json.loads(elements)
    except json.JSONDecodeError:
        element = [c.strip() for c in elements.split(",") if c.strip()]

    # 如果element为all则选择全部参数
    if len(element) == 1 and element[0] == "all":
        element = cfg.ALLOWED_ELEMENTS

    # 校验参数名
    for p in element:
        if p not in cfg.ALLOWED_ELEMENTS:
            return {
                "status": status.HTTP_400_BAD_REQUEST,
                "message": {
                    f"Invalid class: {p}",
                    f"Legal class: {cfg.ALLOWED_ELEMENTS}",
                },
            }

    # 如果表不存在则直接返回无数据
    table_name = f"table_{station_name}_{date}"
    if not postgresql.table_exists(table_name):
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "无数据",
        }

    # 异步绘图，防止阻塞线程
    try:
        file_name, image_id = await asyncio.to_thread(
            plot.setup, station_name, table_name, element
        )
        image_token = str(uuid.uuid4())
        data = {
            "file_name": file_name,
            "image_token": image_token,
            "create_time": int(time.time()),
        }
        postgresql.insert_data("image_tokens", data)

        return {
            "status": status.HTTP_200_OK,
            "image_id": image_id,
            "url": f"http://127.0.0.1:7763/image?image_token={image_token}",
        }
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"绘图发生错误，错误信息：{e}",
        }


@router.get("/image")
async def image(image_token: str) -> FileResponse:
    """
    显示图片资源

    参数:
        image_token: 图片访问令牌 (str)

    返回:
        FileResponse: 图片文件响应

    异常:
        HTTPException: 403 - URL无效或已过期/已使用
    """
    result = postgresql.search_data("image_tokens", "image_token", image_token)
    data = (
        None if result is None else next(iter(result.to_dict(orient="index").values()))
    )
    if not data:
        raise HTTPException(status_code=403, detail="URL无效或已过期/已使用")

    _, file_name = data["create_time"], data["file_name"]

    # 一次性 token：消费后移除，文件由清理线程回收
    postgresql.delete_row("image_tokens", "image_token", image_token)
    return FileResponse(os.path.join("images", file_name))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """
    Favicon endpoint

    返回:
        Response: 204 No Content响应
    """
    return Response(status_code=204)
