from services import utils as tools
from fastapi import APIRouter, status
import os
import time
import pandas as pd

# 可上传的气象元素字段（与模型 tools.element 对齐）
ELEMENT_FIELDS = [
    "temperature",
    "pressure",
    "relative_humidity",
    "wind_speed",
    "wind_direction",
]

# 设置路由
router = APIRouter(
    tags=["post"],  # 在 OpenAPI 文档中为这些路由添加一个标签
)


# 上传站点数据
@router.post("/api/upload")
async def api_upload(item: tools.element):
    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())

    today = time.strftime("%Y-%m-%d", time.localtime(timestamp))
    file_name = f"{station_name}_{today}.csv"
    file_path = os.path.join("data", file_name)

    # 构建写入行：元素为空用 "NULL" 占位
    row = {
        "station_name": station_name,
        "timestamp": timestamp,
        **{
            k: (getattr(item, k) if getattr(item, k) is not None else "NULL")
            for k in ELEMENT_FIELDS
        },
    }

    try:
        df = pd.DataFrame([row])
        df.to_csv(
            file_path,
            index=False,
            header=not os.path.exists(file_path),
            sep="|",
            mode="a",
        )
    except Exception as e:
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"write data failed: {e}",
            "data": None,
        }

    return {"status": status.HTTP_200_OK, "message": "upload success", "data": row}
