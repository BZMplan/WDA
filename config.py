from datetime import datetime
from typing import Optional
from fastapi import Query
from pydantic import BaseModel, field_validator
import time


ALLOWED_ELEMENTS = [
    "temperature",
    "pressure",
    "relative_humidity",
    "dew_point",
    "sea_level_pressure",
    "wind_speed",
    "wind_direction",
]

ELEMENTS = [
    ("temperature", "气温", "°C", "red"),
    ("pressure", "压强", "hPa", "blue"),
    ("relative_humidity", "相对湿度", "%", "green"),
    ("dew_point", "露点", "°C", "red"),
    ("sea_level_pressure", "海压", "hPa", "blue"),
    ("wind_speed", "风速", "m/s", "yellow"),
    ("wind_direction", "风向", "°", "black"),
]


DB_NAME = "data/database/record.db"


class location(BaseModel):
    deviceID: Optional[str] = None  # 设备名称
    locationTimestamp_since1970: Optional[float] = None  # 设备时间戳
    time_utc: Optional[datetime] = None  # utc时间
    time_local: Optional[datetime] = None  # 本地时间
    locationAltitude: Optional[float] = None  # 海拔
    locationLatitude: Optional[float] = None  # 纬度
    locationLongitude: Optional[float] = None  # 经度
    locationSpeed: Optional[float] = None  # 速度
    locationHorizontalAccuracy: Optional[float] = None  # 水平精确度

    @field_validator("locationTimestamp_since1970")
    @classmethod
    def check_timestamp(cls, v):
        now = time.time()
        if v is None:
            return int(v)
        elif abs(now - v) > 10:
            return int((now + v) / 2)
        else:
            return int(v)

    class Config:
        extra = "ignore"


class meteorological_elements(BaseModel):
    station_name: str = None  # 站点名称
    timestamp: Optional[int] = None  # 时间戳
    time_utc: Optional[datetime] = None  # utc时间
    time_local: Optional[datetime] = None  # 本地时间
    temperature: Optional[float] = None  # 气温
    pressure: Optional[float] = None  # 气压
    relative_humidity: Optional[float] = None  # 相对湿度
    dew_point: Optional[float] = None  # 露点
    sea_level_pressure: Optional[float] = None  # 海压
    wind_speed: Optional[float] = None  # 风速
    wind_direction: Optional[float] = None  # 风向

    # @field_validator("timestamp")
    # @classmethod
    # def check_timestamp(cls, v):
    #     now = int(time.time())
    #     if v is None:
    #         return v
    #     if abs(now - v) > 10:
    #         raise ValueError("timestamp may be wrong, please check it.")
    #     return v

    class Config:
        extra = "ignore"


class queryable_elements(BaseModel):
    station_name: str = None  # 站点名称
    timestamp: Optional[int] = None  # 时间戳
    time_utc: Optional[datetime] = None  # utc时间
    time_local: Optional[datetime] = None  # 本地时间

    class Config:
        extra = "ignore"
