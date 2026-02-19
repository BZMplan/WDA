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
    """
    定位数据模型

    用于接收设备定位数据的 Pydantic 模型

    属性:
        deviceID (Optional[str]): 设备名称
        locationTimestamp_since1970 (Optional[float]): 设备时间戳
        locationAltitude (Optional[float]): 海拔
        locationLatitude (Optional[float]): 纬度
        locationLongitude (Optional[float]): 经度
        locationSpeed (Optional[float]): 速度
        locationHorizontalAccuracy (Optional[float]): 水平精确度
    """

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
        """
        校验时间戳

        参数:
            v: 输入的时间戳值

        返回:
            int: 处理后的时间戳
        """
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
    """
    气象要素数据模型

    用于接收气象站数据的 Pydantic 模型

    属性:
        station_name (str): 站点名称
        timestamp (Optional[int]): 时间戳
        time_utc (Optional[datetime]): UTC时间
        temperature (Optional[float]): 气温
        pressure (Optional[float]): 气压
        relative_humidity (Optional[float]): 相对湿度
        dew_point (Optional[float]): 露点
        sea_level_pressure (Optional[float]): 海压
        wind_speed (Optional[float]): 风速
        wind_direction (Optional[float]): 风向
    """

    station_name: str
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
