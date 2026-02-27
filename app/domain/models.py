import time
from datetime import datetime

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

    """

    deviceID: str | None = None
    locationTimestamp_since1970: float | None = None
    locationAltitude: float | None = None
    locationLatitude: float | None = None
    locationLongitude: float | None = None
    locationSpeed: float | None = None
    locationHorizontalAccuracy: float | None = None

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
            return None
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

    """

    station_name: str
    timestamp: int | None = None
    time_utc: datetime | None = None
    temperature: float | None = None
    pressure: float | None = None
    relative_humidity: float | None = None
    dew_point: float | None = None
    sea_level_pressure: float | None = None
    wind_speed: float | None = None
    wind_direction: float | None = None

    class Config:
        extra = "ignore"
