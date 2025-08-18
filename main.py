from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pandas.io.common import file_exists
from pydantic import BaseModel, Extra
import pandas as pd
import time
from typing import Optional

app = FastAPI()

class Station(BaseModel):
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
        extra = Extra.ignore

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

def verify_token(token: str = Depends(oauth2_scheme)):
    if token not in ALLOWED_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired tokens",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@app.post("/api/upload/station")
async def api_upload_station(item: Station, token: str = Depends(verify_token)):
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

@app.post("/api/upload/test")
async def api_upload_test(item: Station):

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="192.168.137.1", port=80, workers=1)
