from functions import tools
from fastapi import APIRouter, Depends, status
import os
import time
import pandas as pd
import routers.oauth 

# 设置路由
router = APIRouter(
    tags=["post"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)

# 上传站点数据，需要token验证
@router.post("/api/upload/official")
async def api_upload_official(item: tools.element, token: str = Depends(routers.oauth.verify_user_status)):
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
        header=not os.path.exists(f"./data/official/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": data}


# 上传站点数据到test，不需要token验证
@router.post("/api/upload/test")
async def api_upload_test(item: tools.element):
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
        header=not os.path.exists(f"./data/test/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": data}
