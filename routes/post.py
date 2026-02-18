import logging
import os
import time
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, status

import services.config as cfg
from services import utils
from services.postgresql import create_weather_data_table, insert_data, table_exists

router = APIRouter(tags=["post"])

logger = logging.getLogger("uvicorn.app")


@router.post("/api/upload")
async def api_upload(item: cfg.meteorological_elements) -> Dict[str, Any]:
    """
    上传站点数据

    参数:
        item: 气象要素数据模型 (meteorological_elements)

    返回:
        Dict[str, Any]: 包含状态码、消息和数据的字典
    """
    timestamp = item.timestamp or int(time.time())
    day = time.strftime("%Y_%m_%d", time.localtime(timestamp))
    table_name = f"table_{item.station_name}_{day}"

    def nullify(value):
        """统一空值处理函数"""
        return None if value is None else value

    # 计算衍生值
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

    # 构建数据行
    row = {
        "station_name": item.station_name,
        "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp)),
        **{field: nullify(getattr(item, field)) for field in cfg.ALLOWED_ELEMENTS},
        "sea_level_pressure": nullify(sea_level_pressure),
        "dew_point": nullify(dew_point),
    }

    # 数据库操作封装
    try:
        if not table_exists(table_name):
            create_weather_data_table(table_name)
        insert_data(table_name, row)
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"Database write failed: {str(e)}",
            "data": None,
        }

    return {"status": status.HTTP_200_OK, "message": "Upload success", "data": row}


@router.post("/sensorlog")
async def sensorlog(item: cfg.location) -> Dict[str, Any]:
    """
    接收senerlog软件上传的数据

    参数:
        item: 定位数据模型 (location)

    返回:
        Dict[str, Any]: 包含状态码、消息和数据的字典
    """
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
