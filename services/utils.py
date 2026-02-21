import logging
import os
import time
from functools import wraps
from services import sql

logger = logging.getLogger("uvicorn.app")


def _log_after_run(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 1. 执行函数本身
        result = await func(*args, **kwargs)
        # 2. 执行完后发送日志
        logger.info(f"函数 [{func.__name__}] 已成功运行")
        return result

    return wrapper


def clean_expired_image_tokens():
    """
    清理过期的图片

    后台线程函数，每5秒检查一次image_tokens表，
    删除超过120秒的过期图片文件和数据库记录。

    注意:
        此函数包含无限循环，应在后台线程中运行。
    """
    logger.info(f"清理过期图片线程已成功运行")
    while True:
        current_time = time.time()
        result = sql.get_table_data("image_tokens", ["create_time", "file_name"])
        arr = [(row["create_time"], row["file_name"]) for _, row in result.iterrows()]

        expired_files = [
            (create_time, file_name)
            for create_time, file_name in arr
            if current_time - create_time > 120
        ]

        for _, file_name in expired_files:
            file_path = os.path.join("images", file_name)
            os.remove(file_path)
            sql.delete_row("image_tokens", "file_name", file_name)
            logger.info(f"{file_path}过期，已删除")

        time.sleep(5)


def calc_sea_level_pressure(temp_c, pressure_hpa, humidity_percent, altitude_m):
    """
    计算海平面气压（hPa）

    参数:
        temp_c (float): 气温（℃）
        pressure_hpa (float): 测站气压（hPa）
        humidity_percent (float): 相对湿度（%）
        altitude_m (float): 海拔（m）

    返回:
        float: 海平面气压（hPa），保留两位小数
    """
    import math

    g = 9.80665
    Rd = 287.05
    lapse = 0.0065
    epsilon = 0.622
    T = temp_c + 273.15
    RH = humidity_percent / 100.0

    es = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
    e = RH * es
    e = min(e, pressure_hpa * 0.99)

    r = epsilon * e / (pressure_hpa - e)
    q = r / (1 + r)

    Tv = T * (1 + 0.61 * q)
    Tv_mean = Tv + 0.5 * lapse * altitude_m

    p0 = pressure_hpa * math.exp(g * altitude_m / (Rd * Tv_mean))

    return round(p0, 2)


def calc_dew_point(temp_c, humidity_percent):
    """
    计算露点温度（℃）

    参数:
        temp_c (float): 气温（℃）
        humidity_percent (float): 相对湿度（%）

    返回:
        float: 露点温度（℃），保留两位小数

    公式来源:
        Magnus-Tetens 经验公式（适用于 -45℃ ~ 60℃）
    """
    import math

    RH = max(0.1, min(100.0, humidity_percent))
    RH_frac = RH / 100.0

    a = 17.27
    b = 237.7

    gamma = (a * temp_c / (b + temp_c)) + math.log(RH_frac)
    dew_point = (b * gamma) / (a - gamma)

    return round(dew_point, 2)
