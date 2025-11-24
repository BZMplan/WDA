from pandas import DataFrame
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    inspect,
)

DATABASE_url = "postgresql+psycopg2://postgres:eothkl123@192.168.10.126:5432/postgres"
engine = create_engine(DATABASE_url, echo=False)
metadata = MetaData()


def table_exists(table_name: str, schema: str | None = None) -> bool:
    """检测某个表是否存在"""
    insp = inspect(engine)
    return insp.has_table(table_name, schema=schema)


def create_weather_data_table(table_name: str):
    """
    创建一张天气数据表，表结构固定，表名可变。
    如果已存在则直接跳过。
    """
    if table_exists(table_name):
        # print(f"表 {table_name} 已存在，跳过创建")
        return

    table = Table(
        table_name,
        metadata,
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
    )

    metadata.create_all(engine, tables=[table])


def create_image_tokons_table(table_name: str):
    """
    创建一张天气数据表，表结构固定，表名可变。
    如果已存在则直接跳过。
    """
    if table_exists(table_name):
        # print(f"表 {table_name} 已存在，跳过创建")
        return

    table = Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("file_name", String, nullable=False),
        Column("image_token", String, nullable=False),
        Column("create_time", Integer, nullable=False),
    )

    metadata.create_all(engine, tables=[table])


def insert_data(table_name: str, data: dict) -> int | None:
    """
    向指定表插入一行数据。
    data 是 {列名: 值} 的字典。
    返回插入行的主键 id（如果有）。
    """
    if not table_exists(table_name):
        if table_name == "image_tokens":
            create_image_tokons_table("image_tokens")

        raise RuntimeError(f"表 {table_name} 不存在，请先创建")

    # 通过反射加载表结构（不需要 ORM class）
    table = Table(table_name, metadata, autoload_with=engine)

    with engine.begin() as conn:  # 自动事务 + 提交
        result = conn.execute(table.insert().values(**data))
        pk = result.inserted_primary_key
        return pk[0] if pk else None


def get_table_data(table_name: str, columns: list[str]) -> DataFrame:
    if not table_exists(table_name):
        raise RuntimeError(f"表 {table_name} 不存在，请先创建")

    table = Table(table_name, metadata, autoload_with=engine)
    selected_cols = [table.c[col] for col in columns]
    with engine.connect() as conn:
        stmt = table.select().with_only_columns(*selected_cols)
        result = conn.execute(stmt)
        df = DataFrame(result.fetchall(), columns=columns)
    return df


def get_latest_data(table_name: str) -> DataFrame:
    if not table_exists(table_name):
        raise RuntimeError(f"表 {table_name} 不存在，请先创建")

    table = Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as conn:
        stmt = table.select().order_by(table.c.time_utc.desc()).limit(1)
        result = conn.execute(stmt)
        df = DataFrame(result.fetchall(), columns=result.keys())
    return df


def search_data(table_name: str, column: str, value):
    """
    根据表名、列名和数据值，返回匹配的行数据（DataFrame）。
    如果没有找到则返回 None。
    """
    if not table_exists(table_name):
        raise RuntimeError(f"表 {table_name} 不存在，请先创建")

    table = Table(table_name, metadata, autoload_with=engine)
    with engine.connect() as conn:
        stmt = table.select().where(table.c[column] == value)
        result = conn.execute(stmt)
        rows = result.fetchall()
        if not rows:
            return None
        df = DataFrame(rows, columns=result.keys())
    return df


def delete_row(table_name: str, column: str, value) -> int:
    """
    根据表名、列名和数据值，删除匹配的行。
    返回删除的行数。
    """
    if not table_exists(table_name):
        raise RuntimeError(f"表 {table_name} 不存在，请先创建")

    table = Table(table_name, metadata, autoload_with=engine)
    with engine.begin() as conn:
        stmt = table.delete().where(table.c[column] == value)
        result = conn.execute(stmt)
        return result.rowcount
