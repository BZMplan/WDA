import logging
import time

from fastapi import APIRouter, status

import services.elements as cfg
from services import utils
from services.sql import create_weather_data_table, insert_data, table_exists

router = APIRouter(tags=["post","v2"])

logger = logging.getLogger("uvicorn.app")


@router.post("/v2/upload")
async def v2_upload(item: cfg.meteorological_elements):
    station_name = item.station_name
    timestamp = item.timestamp
    temperature = item.temperature
    pressure = item.pressure
    relative_humidity = item.relative_humidity
    wind_speed = item.wind_speed
    wind_direction = item.wind_direction

    dew_point = (
        utils.calc_dew_point(temp_c=temperature, humidity_percent=relative_humidity)
        if all((temperature, relative_humidity))
        else None
    )
    sea_level_pressure = (
        utils.calc_sea_level_pressure(
            temp_c=temperature,
            pressure_hpa=pressure,
            humidity_percent=relative_humidity,
            altitude_m=30.0,
        )
        if all((temperature, pressure, relative_humidity))
        else None
    )

    row = {
        "station_name": station_name,
        "time_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(timestamp)),
        "temperature": temperature,
        "pressure": pressure,
        "relative_humidity": relative_humidity,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "sea_level_pressure": sea_level_pressure,
        "dew_point": dew_point,
    }

    day = time.strftime("%Y_%m_%d", time.localtime(timestamp))
    table_name = f"{station_name}_{day}"

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
