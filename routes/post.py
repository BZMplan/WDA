from fastapi import APIRouter, status
from services import utils
from services.utils import create_table, insert_data, table_exists

import logging
import config as cfg
import os
import time
import pandas as pd


# 设置路由
router = APIRouter(
    tags=["post"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

logger = logging.getLogger("uvicorn.app")


# 上传站点数据
@router.post("/api/upload")
async def api_upload(item: cfg.meteorological_elements):

    # 简化时间处理
    timestamp = item.timestamp or int(time.time())
    day = time.strftime("%Y_%m_%d", time.localtime(timestamp))
    table_name = f"table_{item.station_name}_{day}"

    # 统一空值处理函数
    def nullify(value):
        return "NULL" if value is None else value

    # 计算衍生值（封装到独立函数）
    sea_level_pressure = (
        utils.calc_sea_level_pressure(
            item.temperature, item.pressure, item.relative_humidity, 27.5
        )
        if all((item.temperature, item.pressure, item.relative_humidity))
        else None
    )

    dew_point = (
        utils.calc_dew_point(item.temperature, item.relative_humidity)
        if all((item.temperature, item.relative_humidity))
        else None
    )

    # 构建数据行（使用字典推导式统一处理空值）
    row = {
        "station_name": item.station_name,
        "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp)),
        "time_local": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
        **{field: nullify(getattr(item, field)) for field in cfg.ALLOWED_ELEMENTS},
        "sea_level_pressure": nullify(sea_level_pressure),
        "dew_point": nullify(dew_point),
    }

    # 数据库操作封装
    try:
        # 合并表存在检查和创建
        if not table_exists(cfg.DB_NAME, table_name):
            create_table(cfg.DB_NAME, table_name)
        insert_data(cfg.DB_NAME, table_name, row)
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"Database write failed: {str(e)}",
            "data": None,
        }

    return {"status": status.HTTP_200_OK, "message": "Upload success", "data": row}


# 接收senerlog软件上传的数据
# 暂存
@router.post("/sensorlog")
async def sensorlog(item: cfg.location):
    server_timestamp = int(time.time())
    day = time.strftime("%Y-%m-%d", time.localtime(item.locationTimestamp_since1970))
    file_name = f"{item.deviceID}_{day}.csv"
    file_path = os.path.join("data/sensorlog", file_name)

    row = {
        "device_name": item.deviceID,
        "server_timestamp": server_timestamp,
        "device_timestamp": item.locationTimestamp_since1970,
        "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(server_timestamp)),
        "time_local": time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(server_timestamp)
        ),
        "altitude": item.locationAltitude,
        "latitude": item.locationLatitude,
        "longitude": item.locationLongitude,
        "horizontal_accuracy": item.locationHorizontalAccuracy,
        "speed": item.locationSpeed,
    }

    try:
        df = pd.DataFrame([row])

        df.to_csv(
            file_path,
            index=False,
            header=not os.path.exists(file_path),
            sep=",",
            mode="a",
        )
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"write data failed: {e}",
            "data": None,
        }

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": row}
