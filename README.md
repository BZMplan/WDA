# Weather Data Analyzer & Visualization

这是一个基于 **FastAPI** 的气象站数据上传、查询和数据可视化服务。支持上传气象站数据，查询各类气象要素，并生成对应时间段的曲线图。

---

## 功能介绍

- 上传气象站数据（支持多种气象元素，如温度、气压、湿度等）
- 查询指定站点的最新或指定时间戳的气象数据
- 生成并获取指定日期或最近若干小时的气象数据折线图
- 使用基于token的访问控制保护API接口安全

---

## 技术栈

- Python 3.13+
- FastAPI —— 高性能Web框架
- Pandas —— 数据处理
- Matplotlib & Seaborn —— 数据可视化
- Uvicorn —— ASGI服务器

---

## 文件结构

```
.
├── data/
│   ├── station/        # 存放上传的站点数据CSV文件
│   └── test/           # 测试数据目录
├── image/              # 生成的图片文件目录
├── draw.py             # 数据绘图脚本
├── main.py             # API主程序
├── pyproject.toml      # 项目依赖配置
├── log_config.ini      # 日志配置
└── README.md           # 项目说明文档
```

---

## 环境依赖

请确保使用 Python 3.13 或更高版本

```
pip install -r requirements.txt
```

内容示例（requirements.txt）：
```
colorlog>=6.9.0
fastapi>=0.116.1
matplotlib>=3.10.5
pandas>=2.3.1
pydantic
seaborn>=0.13.2
uvicorn>=0.35.0
```

或使用 `pyproject.toml` 进行依赖管理。

---

## 使用说明

### 启动服务

```
uv run main.py
```

### API接口

- **上传气象数据（需Token）**

  `POST /api/upload/station`

  请求Body示例：

  ```
  {
    "station_name": "station1",
    "timestamp": 1692432000,
    "temperature": 25.6,
    "pressure": 1013.2,
    "relative_humidity": 78.5,
    "wind_speed": 3.2,
    "wind_direction": 180,
    "ground_temperature": 20.1,
    "evaporation_capacity": 0.5,
    "sunshine_duration": 5.0
  }
  ```

- **查询气象数据（需Token）**

  `GET /api/get/station`

  查询参数：

  | 参数          | 说明                  | 备注                   |
  | ------------- | --------------------- | ---------------------- |
  | station_name  | 站点名称              | 必填                   |
  | timestamp     | 时间戳（可选）        | 不指定时返回最新数据   |
  | element       | 气象元素（如temperature等） | 默认为"all"返回所有数据 |

- **获取当天气象参数折线图**

  `GET /api/get/image?date=YYYY-MM-DD&cls=temperature|pressure|relative_humidity`

 返回图片的临时访问URL（有时间有效期）。

---

## 代码示例

来自 `draw.py` 的示例绘图调用：

```
from draw import draw_specific_day

draw_specific_day("./data/test/esp32 test.csv", "temperature", "2025-08-19")
```

---

## 日志与调试

日志采用 `uvicorn` 标准日志格式，方便定位问题。图表文件保存在 `./image/` 目录。

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issues 和 Pull Requests，共同完善本项目。

---

如果你需要帮助或有疑问，请随时联系！
