from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from pandas.io.common import file_exists
from pydantic import BaseModel,Extra
import pandas as pd
import time
from typing import Optional
app = FastAPI()

class Station(BaseModel):
    station_name:Optional[str] = None             #站点名称
    timestamp:Optional[int] = None                #时间戳
    temperature:Optional[float] = None            #气温
    pressure:Optional[float] = None               #气压
    relative_humidity:Optional[float] = None      #相对湿度
    wind_speed:Optional[float] = None             #风速
    wind_direction:Optional[float] = None         #风向
    ground_temperature:Optional[float] = None     #地温
    evaporation_capacity:Optional[float] = None   #蒸发量
    sunshine_duration:Optional[float] = None      #日照时间

    class Config:
        extra = Extra.ignore

ALLOWED_TOKENS = {
    "123",
    "456"
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_token(token:str = Depends(oauth2_scheme)):
    if token not in ALLOWED_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的或已过期的token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token



@app.post('/api/upload/station')
async def api_upload_station(item: Station,token:str = Depends(verify_token)):
    return {"Success!"}

@app.post('/api/upload/test')
async def api_upload_test(item: Station):

    station_name = item.station_name
    timestamp = item.timestamp if item.timestamp is not None else int(time.time())
    temperature = item.temperature
    pressure = item.pressure
    relative_humidity = item.relative_humidity
    wind_speed = item.wind_speed
    wind_direction = item.wind_direction
    ground_temperature = item.ground_temperature
    evaporation_capacity = item.evaporation_capacity
    sunshine_duration = item.sunshine_duration

    data = {
        "station_name":station_name,
        "timestamp":timestamp,
        "temperature":temperature,
        "pressure":pressure,
        "relative_humidity":relative_humidity,
        "wind_speed":wind_speed,
        "wind_direction":wind_direction,
        "ground_temperature":ground_temperature,
        "evaporation_capacity":evaporation_capacity,
        "sunshine_duration":sunshine_duration
            }

    df = pd.DataFrame(data, index=[0])
    df.to_csv(f'{station_name}.csv',index=False,header=not file_exists(f'{station_name}.csv'),sep='|',mode='a')

    return {
        "status":status.HTTP_200_OK
    }
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host="127.0.0.1", port=80, workers=1)