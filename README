
---

# 📌 README

## 项目简介

本项目提供了一个基于 **FastAPI** 的气象站数据上传与存储服务，并配套数据可视化工具。

* `main.py`：提供数据上传接口，支持带鉴权的气象站数据上传和测试上传。
* `draw.py`：从 CSV 文件中读取气象数据并绘制趋势图。
* `pyproject.toml`：依赖与项目配置。

---

## 功能说明

### 1. API 服务 (`main.py`)

提供两个接口：

#### (1) 上传气象站数据（需 Token）

```
POST /api/upload/station
Authorization: Bearer <token>
```

请求体示例（JSON）：

```json
{
  "station_name": "Mplan's Station",
  "timestamp": 1723949940,
  "temperature": 28.5,
  "pressure": 1003.2,
  "relative_humidity": 70,
  "wind_speed": 3.5,
  "wind_direction": 180,
  "ground_temperature": 29.1,
  "evaporation_capacity": 0.2,
  "sunshine_duration": 6.5
}
```

成功响应：

```json
{
  "status": 200,
  "message": "upload success",
  "data": {...}
}
```

数据会保存至：

```
./data/station/<station_name>.csv
```

#### (2) 上传测试数据（无 Token）

```
POST /api/upload/test
```

参数与上面一致，数据保存路径：

```
./data/test/<station_name>.csv
```

---

### 2. 数据绘图工具 (`draw.py`)

可视化气象数据某一指标在指定时间范围内的变化趋势。

调用示例：

```python
from draw import draw

draw(
    file_path="./data/test/Mplan's Station.csv",
    target_column="temperature",
    hours_back=24,
    sep="|",
    zone="Asia/Shanghai"
)
```

会生成一张趋势图并保存为：

```
temperature_trend.png
```

功能特点：

* 支持时区转换（默认：`Asia/Shanghai`）。
* 自动处理缺失值，用红色 `x` 标记。
* 若近 24 小时数据不足，则回退使用全部数据。

---

## 安装与运行

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd <your-repo>
```

### 2. 安装依赖

```bash
uv pip install -e .
```

或直接用 `pip`：

```bash
pip install -r requirements.txt
```

### 3. 启动 API 服务

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：

* Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 配置说明

* Python 版本：`>=3.13`
* 依赖：详见 `pyproject.toml`

  * FastAPI
  * Pandas
  * Matplotlib
  * Uvicorn
  * Seaborn

---

## 项目结构

```
├── main.py              # FastAPI API 服务
├── draw.py              # 数据可视化工具
├── pyproject.toml       # 项目配置与依赖
├── data/                # 存储数据
│   ├── station/         # 鉴权接口上传的数据
│   └── test/            # 测试接口上传的数据
```


