import time
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

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


class location(BaseModel):
    """定位数据模型"""

    deviceID: Optional[str] = None
    locationTimestamp_since1970: Optional[float] = None
    locationAltitude: Optional[float] = None
    locationLatitude: Optional[float] = None
    locationLongitude: Optional[float] = None
    locationSpeed: Optional[float] = None
    locationHorizontalAccuracy: Optional[float] = None

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
    """气象要素数据模型"""

    station_name: str = None
    timestamp: Optional[int] = None
    time_utc: Optional[datetime] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    relative_humidity: Optional[float] = None
    dew_point: Optional[float] = None
    sea_level_pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None

    class Config:
        extra = "ignore"
