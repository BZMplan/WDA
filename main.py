from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pandas.io.common import file_exists
from pydantic import BaseModel
from typing import Optional
import os
import pandas as pd
import time
import math
import threading
import uuid
import draw
import logging
import uvicorn

app = FastAPI()

app.mount("/image", StaticFiles(directory="image"), name="image")

class element(BaseModel):
    station_name: Optional[str] = None  # 站点名称
    timestamp: Optional[int] = None  # 时间戳
    temperature: Optional[float] = None  # 气温
    pressure: Optional[float] = None  # 气压
    relative_humidity: Optional[float] = None  # 相对湿度
    wind_speed: Optional[float] = None  # 风速
    wind_direction: Optional[float] = None  # 风向
    ground_temperature: Optional[float] = None  # 地温
    evaporation_capacity: Optional[float] = None  # 蒸发量
    sunshine_duration: Optional[float] = None  # 日照时间

    class Config:
        extra = "ignore"

class data(BaseModel):
    station_name:str
    timestamp:int = None
    element:str = "all"

ALLOWED_TOKENS = {
    "a0556d20-e469-4b17-a74d-10ee9891adf7",
    "2f02dad5-1a09-40e3-a253-74fa8cd7f13c",
    "2e9de4a5-2f09-46f3-90e3-dc5ba0cd7300",
    "97d6e878-a755-4ccf-b8d5-8262b0ae445b",
    "c4040806-217c-4c30-b7c9-13f9b960fd67",
    "26aea20b-d866-402a-9207-4992f55b02de",
    "d0cd7c2a-762b-4423-b6a5-d1e7e9e37368",
    "685f2104-4099-465b-a465-a1d73001ef73",
    "cb499467-2ef3-4045-83fc-00296b8f05b6",
    "8754080a-2df8-40c7-8765-a66d3721b6af"
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

one_time_tokens = {}

def clean_expired_tokens():
    while True:
        time.sleep(60)  # 每分钟检查一次
        current_time = time.time()
        # 清理300秒（5分钟）前的令牌
        expired_tokens = [t for t, (created_time, _) in one_time_tokens.items() if current_time - created_time > 300]
        for token in expired_tokens:
            del one_time_tokens[token]

def verify_token(token: str = Depends(oauth2_scheme)):
    if token not in ALLOWED_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired tokens",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

def clean_nan_values(data: dict) -> dict:
    """将字典中的NaN值替换为None，确保JSON序列化正常"""
    return {
        key: None if isinstance(value, float) and math.isnan(value) else value
        for key, value in data.items()
    }

threading.Thread(target=clean_expired_tokens, daemon=True).start()

# 上传站点数据，需要token验证
@app.post("/api/upload/station")
async def api_upload_station(item: element, token: str = Depends(verify_token)):
    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())
    temperature = item.temperature if item.temperature is not None else "NULL"
    pressure = item.pressure if item.pressure is not None else "NULL"
    relative_humidity = item.relative_humidity if item.relative_humidity is not None else "NULL"
    wind_speed = item.wind_speed if item.wind_speed is not None else "NULL"
    wind_direction = item.wind_direction if item.wind_direction is not None else "NULL"
    ground_temperature = item.ground_temperature if item.ground_temperature is not None else "NULL"
    evaporation_capacity = item.evaporation_capacity if item.evaporation_capacity is not None else "NULL"
    sunshine_duration = item.sunshine_duration if item.sunshine_duration is not None else "NULL"

    data = {
        "station_name": station_name,
        "timestamp": timestamp,
        "temperature": temperature,
        "pressure": pressure,
        "relative_humidity": relative_humidity,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "ground_temperature": ground_temperature,
        "evaporation_capacity": evaporation_capacity,
        "sunshine_duration": sunshine_duration,
    }

    df = pd.DataFrame(data, index=[0])
    file_name = f"{station_name}.csv"
    df.to_csv(
        f"./data/station/{file_name}",
        index=False,
        header=not file_exists(f"./data/station/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK,"message": "upload success", "data": data}

# 上传站点数据到test，不需要token验证
@app.post("/api/upload/test")
async def api_upload_test(item: element):

    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())
    temperature = item.temperature if item.temperature is not None else "NULL"
    pressure = item.pressure if item.pressure is not None else "NULL"
    relative_humidity = item.relative_humidity if item.relative_humidity is not None else "NULL"
    wind_speed = item.wind_speed if item.wind_speed is not None else "NULL"
    wind_direction = item.wind_direction if item.wind_direction is not None else "NULL"
    ground_temperature = item.ground_temperature if item.ground_temperature is not None else "NULL"
    evaporation_capacity = item.evaporation_capacity if item.evaporation_capacity is not None else "NULL"
    sunshine_duration = item.sunshine_duration if item.sunshine_duration is not None else "NULL"

    data = {
        "station_name": station_name,
        "timestamp": timestamp,
        "temperature": temperature,
        "pressure": pressure,
        "relative_humidity": relative_humidity,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "ground_temperature": ground_temperature,
        "evaporation_capacity": evaporation_capacity,
        "sunshine_duration": sunshine_duration,
    }

    df = pd.DataFrame(data, index=[0])
    file_name = f"{station_name}.csv"
    df.to_csv(
        f"./data/test/{file_name}",
        index=False,
        header=not file_exists(f"./data/test/{file_name}"),
        sep="|",
        mode="a",
    )

    return {"status": status.HTTP_200_OK,"message": "upload success", "data": data}

# 获取站点数据，需要token验证
@app.get("/api/get/station")
async def api_get_station(item: data,token:str = Depends(verify_token)):
    #未指定时间戳时，返回最新数据
    if item.timestamp is None:
        file_name = f"{item.station_name}.csv"
        df = pd.read_csv(f"./data/station/{file_name}", sep="|")
        
        if item.element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].to_dict(orient="records")[-1]
        else:
            if item.element not in df.columns:
                return {"status": status.HTTP_400_BAD_REQUEST, "message": "element not found", "data": None}
            result = df[["station_name","timestamp", item.element]].to_dict(orient="records")[-1]
            if not result:
                return {"status": status.HTTP_404_NOT_FOUND, "message": "no data found", "data": None}    
        
        result = clean_nan_values(result)
        return {"status": status.HTTP_200_OK, "message": "query success", "data": result}
    #指定时间戳时，返回该时间戳的数据
    else:
        file_name = f"{item.station_name}.csv"
        df = pd.read_csv(f"./data/station/{file_name}", sep="|")
        
        if item.element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].loc[df["timestamp"] == item.timestamp].to_dict(orient="records")[-1]
        else:
            if item.element not in df.columns:
                return {"status": status.HTTP_400_BAD_REQUEST, "message": "element not found", "data": None}
            result = df[["station_name","timestamp", item.element]].loc[df["timestamp"] == item.timestamp].to_dict(orient="records")[-1]
            if not result:
                return {"status": status.HTTP_404_NOT_FOUND, "message": "no data found", "data": None}    
        
        result = clean_nan_values(result)
        return {"status": status.HTTP_200_OK, "message": "query success", "data": result}

# 获取站点数据从test，不需要token验证
@app.get("/api/get/test")
async def api_get_test(item: data):
    
    #未指定时间戳时，返回最新数据
    if item.timestamp is None:
        file_name = f"{item.station_name}.csv"
        df = pd.read_csv(f"./data/test/{file_name}", sep="|")
        
        if item.element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].to_dict(orient="records")[-1]
        else:
            if item.element not in df.columns:
                return {"status": status.HTTP_400_BAD_REQUEST, "message": "element not found", "data": None}
            result = df[["station_name","timestamp", item.element]].to_dict(orient="records")[-1]
            if not result:
                return {"status": status.HTTP_404_NOT_FOUND, "message": "no data found", "data": None}    
        
        result = clean_nan_values(result)
        return {"status": status.HTTP_200_OK, "message": "query success", "data": result}
    #指定时间戳时，返回该时间戳的数据
    else:
        file_name = f"{item.station_name}.csv"
        df = pd.read_csv(f"./data/test/{file_name}", sep="|")
        
        if item.element == "all":
            result = df[["station_name", "timestamp"] + list(df.columns[2:])].loc[df["timestamp"] == item.timestamp].to_dict(orient="records")[-1]
        else:
            if item.element not in df.columns:
                return {"status": status.HTTP_400_BAD_REQUEST, "message": "element not found", "data": None}
            result = df[["station_name","timestamp", item.element]].loc[df["timestamp"] == item.timestamp].to_dict(orient="records")[-1]
            if not result:
                return {"status": status.HTTP_404_NOT_FOUND, "message": "no data found", "data": None}    
        
        result = clean_nan_values(result)
        return {"status": status.HTTP_200_OK, "message": "query success", "data": result}

# 发送请求获取对应图片的url
@app.get("/api/get/image")
async def api_get_image(date:str, cls:str):
    allowed_cls = ["temperature","pressure","relative_humidity"]
    if cls in allowed_cls:
        draw.draw_specific_day("./data/test/esp32 test.csv",f"{cls}",date,sep='|',zone='Asia/Shanghai')

        token = str(uuid.uuid4())
        resource_path = f"{cls}_{date}.png"
        one_time_tokens[token] = (time.time(), resource_path)
        return {"url":f"http://127.0.0.1/image?token={token}"}
    else:
        logger.warning(f"不支持的类型:{cls}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not Support class:{cls}"
        )
        
# 显示图片资源
@app.get("/image")
async def image(token:str):
    if token not in one_time_tokens:
        raise HTTPException(status_code=403, detail="URL无效或已被使用")
    
    created_time, resource_path = one_time_tokens.pop(token)
    
    if time.time() - created_time > 300:
        raise HTTPException(status_code=403, detail="URL已过期")
    
    # 返回静态资源
    return FileResponse(os.path.join("image", resource_path))

if __name__ == "__main__":
    
    #启动服务端
    
    logger = logging.getLogger("uvicorn.app")
    uvicorn.run(app=app, host="0.0.0.0", port=80, workers=1,log_config="./log_config.ini")
    
