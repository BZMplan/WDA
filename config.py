from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator
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

class meteorological_elements(BaseModel):
    station_name: Optional[str] = None  # 站点名称
    timestamp: Optional[int] = None  # 时间戳
    time_utc: Optional[datetime] = None
    time_local: Optional[datetime] = None
    temperature: Optional[float] = None  # 气温
    pressure: Optional[float] = None  # 气压
    relative_humidity: Optional[float] = None  # 相对湿度
    dew_point: Optional[float] = None
    sea_level_pressure: Optional[float] = None
    wind_speed: Optional[float] = None  # 风速
    wind_direction: Optional[float] = None  # 风向

    class Config:
        extra = "ignore"

    @validator("timestamp")
    def check_timestamp(cls, v):
        now = int(time.time())
        if v is None:
            return v
        if abs(now - v) > 10:
            raise ValueError("timestamp may be wrong, please check it.")
        return v
