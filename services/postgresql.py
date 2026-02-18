import logging
from typing import Any, Dict, List, Optional

from pandas import DataFrame
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    inspect,
    select,
)
from sqlalchemy.engine import Engine

from services.load_config import CONFIG

logger = logging.getLogger("uvicorn.app")

username = CONFIG.get("postgresql", {}).get("username")
password = CONFIG.get("postgresql", {}).get("password")
host = CONFIG.get("postgresql", {}).get("host")
port = CONFIG.get("postgresql", {}).get("port")
database = CONFIG.get("postgresql", {}).get("database")
DATABASE_URL = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

engine: Engine = create_engine(DATABASE_URL, echo=False)
metadata: MetaData = MetaData()
_TABLE_CACHE: Dict[str, Table] = {}


def get_table(table_name: str) -> Table:
    """
    从缓存或数据库中获取 Table 对象。
    如果缓存中没有，则尝试通过反射（autoload）加载。
    """
    if table_name in _TABLE_CACHE:
        return _TABLE_CACHE[table_name]

    insp = inspect(engine)
    if not insp.has_table(table_name):
        raise RuntimeError(f"表 {table_name} 不存在，请先创建。")

    table = Table(table_name, metadata, autoload_with=engine)
    _TABLE_CACHE[table_name] = table
    return table


def table_exists(table_name: str, schema: Optional[str] = None) -> bool:
    """检测某个表是否存在"""
    insp = inspect(engine)
    return insp.has_table(table_name, schema=schema)


def _define_and_create_table(table_name: str, columns: List[Column]):
    """私有通用方法：定义并创建表"""
    if table_exists(table_name):
        try:
            get_table(table_name)
        except RuntimeError:
            pass
        return

    table = Table(table_name, metadata, *columns)
    metadata.create_all(engine, tables=[table])
    _TABLE_CACHE[table_name] = table


def create_weather_data_table(table_name: str):
    """创建天气数据表"""
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("station_name", String(64), nullable=False),
        Column("time_utc", DateTime, nullable=False),
        Column("temperature", Float, nullable=True),
        Column("pressure", Float, nullable=True),
        Column("relative_humidity", Float, nullable=True),
        Column("dew_point", Float, nullable=True),
        Column("sea_level_pressure", Float, nullable=True),
        Column("wind_speed", Float, nullable=True),
        Column("wind_direction", Float, nullable=True),
    ]
    _define_and_create_table(table_name, columns)


def create_image_tokons_table(table_name: str):
    """创建图片 Token 映射表"""
    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("file_name", String, nullable=False, unique=True),
        Column("image_token", String, nullable=False),
        Column("create_time", Integer, nullable=False),
    ]
    _define_and_create_table(table_name, columns)


def insert_data(table_name: str, data: Dict[str, Any]) -> Optional[int]:
    """
    向指定表插入一行数据。
    data 是 {列名: 值} 的字典。
    返回插入行的主键 id（如果有）。
    """
    if not table_exists(table_name) and table_name == "image_tokens":
        create_image_tokons_table(table_name)

    table = get_table(table_name)

    with engine.begin() as conn:
        result = conn.execute(table.insert().values(**data))
        pk = result.inserted_primary_key
        return pk[0] if pk else None


def get_table_data(table_name: str, columns: List[str]) -> DataFrame:
    """获取指定列的所有数据"""
    table = get_table(table_name)
    selected_cols = [table.c[col] for col in columns]

    with engine.connect() as conn:
        stmt = select(*selected_cols)
        result = conn.execute(stmt)
        df = DataFrame(result.fetchall(), columns=columns)
    return df


def get_latest_data(table_name: str, time_column: str = "time_utc") -> DataFrame:
    """获取表中最新的单条数据，默认按 time_utc 排序"""
    table = get_table(table_name)

    if time_column not in table.c:
        time_column = "id"

    with engine.connect() as conn:
        stmt = select(table).order_by(table.c[time_column].desc()).limit(1)
        result = conn.execute(stmt)
        df = DataFrame(result.fetchall(), columns=result.keys())
    return df


def search_data(table_name: str, column: str, value: Any) -> Optional[DataFrame]:
    """
    根据表名、列名和数据值，返回匹配的行数据（DataFrame）。
    """
    table = get_table(table_name)

    with engine.connect() as conn:
        stmt = select(table).where(table.c[column] == value)
        result = conn.execute(stmt)

        rows = result.fetchall()
        if not rows:
            return None
        df = DataFrame(rows, columns=result.keys())
    return df


def delete_row(table_name: str, column: str, value: Any) -> int:
    """
    根据表名、列名和数据值，删除匹配的行。
    返回删除的行数。
    """
    table = get_table(table_name)

    with engine.begin() as conn:
        stmt = delete(table).where(table.c[column] == value)
        result = conn.execute(stmt)
        return result.rowcount
