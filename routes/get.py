from datetime import datetime
from fastapi import APIRouter, HTTPException, Response, status, Query
from fastapi.responses import FileResponse
from services import postgresql
from services import plot
import services.config as cfg
import uuid
import json
import time
import pandas as pd
import os
import asyncio
import logging

# 设置路由
router = APIRouter(
    tags=["get"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

logger = logging.getLogger("uvicorn.app")


# 获取实时站点数据
@router.get("/api/get/info")
async def api_get_info(
    station_name: str = None,
):
    station_name = station_name
    timestamp = int(time.time())

    day = time.strftime("%Y_%m_%d", time.localtime(timestamp))
    table_name = f"table_{station_name}_{day}"

    # 如果表不存在，则直接范围无数据
    if not postgresql.table_exists(table_name):
        return {
            "status": status.HTTP_404_NOT_FOUND,
            "message": "无数据",
            "data": None,
        }
    data = postgresql.get_latest_data(table_name)
    if data is not None and isinstance(data, pd.DataFrame):
        data = data.to_dict(orient="records")
    logging.info("数据查询成功")
    return {"status": status.HTTP_200_OK, "message": "成功获取数据", "data": data}


# 发送请求获取对应图片的url
@router.get("/api/get/image")
async def api_get_image(
    station_name: str,
    date: str = None,
    elements: str = Query(...),
):
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


# 显示图片资源
@router.get("/image")
async def image(image_token: str):
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
async def favicon():
    # return FileResponse(os.path.join("static", "favicon.ico"))
    return Response(status_code=204)
