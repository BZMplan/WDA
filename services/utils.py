import logging
import math
import os
import time
import sqlite3

from config import DB_NAME

logger = logging.getLogger("uvicorn.app")

# 后续将存贮在数据库里
one_time_image_tokens = {}

def clean_expired_image_tokens():

    while True:
        time.sleep(10)  # 每10秒检查一次
        current_time = time.time()
        # 清理120秒（2分钟）前的令牌
        expired_tokens = [
            t
            for t, (created_time, _) in one_time_image_tokens.items()
            if current_time - created_time > 120
        ]
        for image_token in expired_tokens:
            # 删除token和对应的文件
            _, resource_path = one_time_image_tokens[image_token]
            os.remove(os.path.join("images", resource_path))
            # logger.info(f"图片'{os.path.join("images",resource_path)}'过期，已删除")
            img_path = os.path.join("images", resource_path)
            logger.info(f"图片'{img_path}'过期,已删除")
            del one_time_image_tokens[image_token]


def clean_nan_values(data: dict) -> dict:
    """将字典中的NaN值替换为None,确保JSON序列化正常"""
    return {
        key: None if isinstance(value, float) and math.isnan(value) else value
        for key, value in data.items()
    }


# 数据库相关操作
def table_exists(table_name):
    """
    检查SQLite数据库中是否存在指定的表

    Args:
        db_name (str): 数据库文件名
        table_name (str): 要检查的表名

    Returns:
        bool: 如果表存在返回True，否则返回False
    """
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 方法1：查询sqlite_master系统表（最可靠）
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """,
            (table_name,),
        )

        # 获取查询结果
        result = cursor.fetchone()

        return result is not None

    except sqlite3.Error as e:
        print(f"查询表时出错: {e}")
        return False
    finally:
        if conn:
            conn.close()

def create_table(table_name):
    # 创建数据库连接
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT NOT NULL,
            time_utc DATETIME NOT NULL,
            time_local DATETIME NOT NULL,
            temperature REAL,
            pressure REAL,
            relative_humidity REAL,
            dew_point REAL,
            sea_level_pressure REAL,
            wind_speed REAL,
            wind_direction INTEGER,
            UNIQUE(station_name, time_utc, time_local)
        );
        """
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"创建成功：{table_name}")
    except sqlite3.Error as e:
        logger.error(f"创建表时出错:{e}")
    finally:
        conn.close()

def insert_record(table_name, record_data):
    """
    向weather_records表中插入单行气象数据

    Args:
        record_data (dict): 包含气象数据的字典
    """
    # 连接数据库
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # 插入SQL语句（使用INSERT OR IGNORE避免重复数据）
        insert_sql = f"""
        INSERT OR IGNORE INTO {table_name} 
        (station_name, time_utc, time_local, temperature, pressure, 
         relative_humidity, dew_point, sea_level_pressure, wind_speed, wind_direction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # 执行插入
        cursor.execute(
            insert_sql,
            (
                record_data["station_name"],
                record_data["time_utc"],
                record_data["time_local"],
                record_data["temperature"],
                record_data["pressure"],
                record_data["relative_humidity"],
                record_data["dew_point"],
                record_data["sea_level_pressure"],
                record_data["wind_speed"],
                record_data["wind_direction"],
            ),
        )

        conn.commit()

        if cursor.rowcount > 0:
            logger.info("数据插入成功！")
        else:
            logger.warning("数据已存在，未插入重复记录!")

    except sqlite3.Error as e:
        print(f"插入数据时出错: {e}")
    finally:
        conn.close()

def get_latest_record(table_name, order_column='id', is_desc=True):
    """
    查询表中的最新一行数据
    
    Args:
        db_path (str): 数据库文件路径
        table_name (str): 表名
        order_column (str): 用于排序的列名（通常是ID或时间列）
        is_desc (bool): 是否降序排列（True表示最新的在前）
        
    Returns:
        dict or None: 包含最新记录的字典，无数据时返回None
    """
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # 启用行工厂，便于按列名访问
        
        # 构建查询SQL
        order_dir = "DESC" if is_desc else "ASC"
        query = f"""
            SELECT * FROM {table_name}
            ORDER BY {order_column} {order_dir}
            LIMIT 1
        """
        
        # 执行查询
        cursor = conn.cursor()
        cursor.execute(query)
        
        # 获取结果
        row = cursor.fetchone()
        
        if row:
            # 转换为字典返回
            return dict(row)
        else:
            print(f"表 '{table_name}' 中没有数据")
            return None
            
    except sqlite3.Error as e:
        print(f"查询出错: {e}")
        return None
    finally:
        if conn:
            conn.close()