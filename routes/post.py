from fastapi import APIRouter, status
import config as cfg
import os
import time
import pandas as pd
import math


# 设置路由
router = APIRouter(
    tags=["post"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)


# 上传站点数据
@router.post("/api/upload")
async def api_upload(item: cfg.meteorological_elements):
    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())

    day = time.strftime("%Y-%m-%d", time.localtime(timestamp))
    file_name = f"{station_name}_{day}.csv"
    file_path = os.path.join("data", file_name)

    element_values = {field: getattr(item, field) for field in cfg.ALLOWED_ELEMENTS}

    # 计算海压
    sea_level_pressure = None
    if (
        element_values["pressure"] is not None
        and element_values["temperature"] is not None
        and element_values["relative_humidity"] is not None
    ):
        sea_level_pressure = calc_sea_level_pressure(
            element_values["temperature"],
            element_values["pressure"],
            element_values["relative_humidity"],
            27.5,
        )

    # 计算露点温度
    dew_point = None
    if (
        element_values["temperature"] is not None
        and element_values["relative_humidity"] is not None
    ):
        dew_point = calc_dew_point(
            element_values["temperature"], element_values["relative_humidity"]
        )

    # 构建写入行：元素为空用 "NULL" 占位
    row = {
        "station_name": station_name,
        "timestamp": timestamp,
        "time_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime(timestamp)),
        "time_local": time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp)),
        **{
            k: (element_values[k] if element_values[k] is not None else "NULL")
            for k in cfg.ALLOWED_ELEMENTS
        },
        "sea_level_pressure": (
            sea_level_pressure if sea_level_pressure is not None else "NULL"
        ),
        "dew_point": dew_point if dew_point is not None else "NULL",
    }

    try:
        df = pd.DataFrame([row])

        # 替换NULL为NaN（方便后续计算）
        df[cfg.ALLOWED_ELEMENTS] = df[cfg.ALLOWED_ELEMENTS].replace("NULL", pd.NA)

        # 按站点和分钟分组，计算平均值，保留两位小数
        tmp = (
            df.groupby(["station_name", "time_utc", "time_local"])[cfg.ALLOWED_ELEMENTS]
            .mean()
            .reset_index()
            .round(2)
        )

        created = False
        # 若csv文件未被创建则先创建
        if not os.path.exists("data/tmp.csv"):
            tmp.to_csv(
                "data/tmp.csv",
                index=False,
                header=not os.path.exists("data/tmp.csv"),
                sep=",",
                mode="a",
            )
            created = True

        tmp_df = pd.read_csv("data/tmp.csv")

        if tmp["time_utc"].values != tmp_df["time_utc"].iloc[-1]:
            df = (
                tmp_df.groupby(["station_name", "time_utc", "time_local"])[
                    cfg.ALLOWED_ELEMENTS
                ]
                .mean()
                .reset_index()
                .round(2)
            )
            df.to_csv(
                file_path,
                index=False,
                header=not os.path.exists(file_path),
                sep=",",
                mode="a",
            )
            os.remove("data/tmp.csv")
        if not created:
            tmp.to_csv(
                "data/tmp.csv",
                index=False,
                header=not os.path.exists("data/tmp.csv"),
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


# sea_level_pressure
def calc_sea_level_pressure(temp_c, pressure_hpa, humidity_percent, altitude_m):
    """
    计算海平面气压（hPa）
    参数：
        temp_c:            气温（℃）
        pressure_hpa:      测站气压（hPa）
        humidity_percent:  相对湿度（%）
        altitude_m:        海拔（m）
    返回：
        海平面气压（hPa）
    """
    # 常数
    g = 9.80665  # 重力加速度 (m/s^2)
    Rd = 287.05  # 干空气气体常数 (J/(kg·K))
    lapse = 0.0065  # 标准直减率 (K/m)
    epsilon = 0.622  # Rv/Rd 倒数
    T = temp_c + 273.15  # 转换为开尔文温度
    RH = humidity_percent / 100.0

    # 饱和水汽压（Magnus公式）
    es = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
    e = RH * es  # 实际水汽压
    e = min(e, pressure_hpa * 0.99)  # 防止 e 超过气压

    # 混合比 (kg/kg)
    r = epsilon * e / (pressure_hpa - e)
    q = r / (1 + r)  # 比湿

    # 虚温 (K)
    Tv = T * (1 + 0.61 * q)

    # 平均虚温修正（向下延伸到海平面一半高度）
    Tv_mean = Tv + 0.5 * lapse * altitude_m

    # Hypsometric 方程：p0 = p * exp(g*z / (Rd*Tv_mean))
    p0 = pressure_hpa * math.exp(g * altitude_m / (Rd * Tv_mean))

    return round(p0, 2)


# dew_point
def calc_dew_point(temp_c, humidity_percent):
    """
    计算露点温度（℃）
    参数：
        temp_c: 气温（℃）
        humidity_percent: 相对湿度（%）
    返回：
        露点温度（℃）
    公式来源：
        Magnus-Tetens 经验公式（适用于 -45℃ ~ 60℃）
    """
    # 保证 RH 在 [0.1, 100] 之间，防止 log(0)
    RH = max(0.1, min(100.0, humidity_percent))
    RH_frac = RH / 100.0

    # Magnus 常数（针对水面）
    a = 17.27
    b = 237.7  # ℃

    # 计算 γ 函数
    gamma = (a * temp_c / (b + temp_c)) + math.log(RH_frac)

    # 计算露点
    dew_point = (b * gamma) / (a - gamma)
    return round(dew_point, 2)
