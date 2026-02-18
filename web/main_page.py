import asyncio
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

router = APIRouter()

clients = set()
DATA_FILE = Path("data/sensorlog/iphone_2025-11-07.csv")
STALE_THRESHOLD = timedelta(minutes=1)


@router.get("/data")
def get_data():
    """
    获取定位数据

    读取 CSV 文件并返回所有定位数据。

    返回:
        JSONResponse: 包含定位数据的 JSON 响应
    """
    df = pd.read_csv(DATA_FILE)
    df = df.dropna(subset=["latitude", "longitude"])
    return JSONResponse(df.to_dict(orient="records"))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点，实时推送定位数据

    每 2 秒推送一次最新位置数据，如果数据超过 1 分钟则标记为过期。

    参数:
        websocket (WebSocket): WebSocket 连接对象
    """
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            latest, timestamp = _load_latest_record()

            if not latest:
                await websocket.send_json(
                    {
                        "stale": True,
                        "message": "暂无定位数据",
                        "last_time": None,
                    }
                )
            elif _is_stale(timestamp):
                await websocket.send_json(
                    {
                        "stale": True,
                        "message": "最新定位已超过 1 分钟，已暂停展示",
                        "last_time": _format_timestamp(timestamp),
                    }
                )
            else:
                latest["longitude"], latest["latitude"] = wgs84_to_gcj02(
                    latest["longitude"], latest["latitude"]
                )
                latest["stale"] = False
                latest["last_time"] = _format_timestamp(timestamp)
                await websocket.send_json(latest)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        clients.remove(websocket)


def _load_latest_record() -> Tuple[Optional[dict], Optional[datetime]]:
    """
    加载最新记录

    返回:
        Tuple[Optional[dict], Optional[datetime]]: (最新记录字典, 时间戳)
    """
    if not DATA_FILE.exists():
        return None, None
    try:
        df = pd.read_csv(DATA_FILE)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return None, None

    df = df.dropna(subset=["latitude", "longitude"])
    if df.empty:
        return None, None

    latest = df.iloc[-1].to_dict()
    timestamp = _extract_timestamp(latest)
    return latest, timestamp


def _extract_timestamp(record: dict) -> Optional[datetime]:
    """
    从记录中提取时间戳

    参数:
        record (dict): 数据记录

    返回:
        Optional[datetime]: 提取的时间戳或 None
    """
    for field in ("time_local", "time_utc"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.strip())
            except ValueError:
                continue

    for field in ("server_timestamp", "device_timestamp"):
        value = record.get(field)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        try:
            return datetime.fromtimestamp(float(value))
        except (ValueError, OSError, TypeError):
            continue
    return None


def _is_stale(timestamp: Optional[datetime]) -> bool:
    """
    检查数据是否过期

    参数:
        timestamp (Optional[datetime]): 时间戳

    返回:
        bool: 是否过期（超过1分钟）
    """
    if timestamp is None:
        return True
    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    return now - timestamp > STALE_THRESHOLD


def _format_timestamp(timestamp: Optional[datetime]) -> Optional[str]:
    """
    格式化时间戳

    参数:
        timestamp (Optional[datetime]): 时间戳

    返回:
        Optional[str]: 格式化后的字符串或 None
    """
    if not timestamp:
        return None
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def wgs84_to_gcj02(lon, lat):
    """
    WGS84 坐标系转 GCJ02 坐标系（火星坐标系）

    参数:
        lon (float): 经度
        lat (float): 纬度

    返回:
        Tuple[float, float]: (转换后的经度, 转换后的纬度)
    """
    a = 6378245.0
    ee = 0.00669342162296594323
    if lon < 72.004 or lon > 137.8347 or lat < 0.8293 or lat > 55.8271:
        return lon, lat
    dlat = _transform_lat(lon - 105.0, lat - 35.0)
    dlon = _transform_lon(lon - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * math.pi)
    dlon = (dlon * 180.0) / (a / sqrtmagic * math.cos(radlat) * math.pi)
    mglat = lat + dlat
    mglon = lon + dlon
    return mglon, mglat


def _transform_lat(x, y):
    """
    坐标转换辅助函数 - 纬度变换

    参数:
        x (float): x 坐标差值
        y (float): y 坐标差值

    返回:
        float: 变换后的纬度偏移量
    """
    ret = (
        -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    )
    ret += (
        (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi))
        * 2.0
        / 3.0
    )
    ret += (
        (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    )
    ret += (
        (160.0 * math.sin(y / 12.0 * math.pi) + 320 * math.sin(y * math.pi / 30.0))
        * 2.0
        / 3.0
    )
    return ret


def _transform_lon(x, y):
    """
    坐标转换辅助函数 - 经度变换

    参数:
        x (float): x 坐标差值
        y (float): y 坐标差值

    返回:
        float: 变换后的经度偏移量
    """
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (
        (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi))
        * 2.0
        / 3.0
    )
    ret += (
        (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    )
    ret += (
        (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi))
        * 2.0
        / 3.0
    )
    return ret
