import logging
import math
import os
import time

from services import postgresql


logger = logging.getLogger("uvicorn.app")


# 清理过期的图片
def clean_expired_image_tokens():

    while True:
        current_time = time.time()
        # 清理120秒（2分钟）前的令牌
        result = postgresql.get_table_data("image_tokens", ["create_time", "file_name"])
        arr = [(row["create_time"], row["file_name"]) for _, row in result.iterrows()]

        expired_files = [
            (create_time, file_name)
            for create_time, file_name in arr
            if current_time - create_time > 120
        ]

        for _, file_name in expired_files:
            file_path = os.path.join("images", file_name)
            os.remove(file_path)
            postgresql.delete_row("image_tokens", "file_name", file_name)
            logger.info(f"{file_path}过期，已删除")

        time.sleep(5)  # 每5秒检查一次


# 数值计算功能函数
# 计算海平面气压
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


# 计算露点温度
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
