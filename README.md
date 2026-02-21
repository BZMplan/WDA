# Weather Data Analyzer & Visualization

一个基于 **FastAPI** 的气象站数据上传、查询与可视化服务，使用 PostgreSQL 持久化观测值，支持 Matplotlib 异步绘图，并通过一次性令牌控制图片访问。

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/BZMplan/WDA)

---

## 功能亮点

- **实时采集与补算**：`POST /api/upload` 接收站点分钟级观测，自动补算露点温度与海平面气压（当气温/气压/湿度齐全时）。
- **PostgreSQL 持久化**：按"站点 + 日期"自动创建表 `{station}_{YYYY_MM_DD}`，图片令牌记录在 `image_tokens` 表中。
- **可视化服务**：异步生成 Matplotlib 折线图，字体路径由 `sql_config.yaml` 配置，支持多要素多子图。
- **安全的图片访问**：每张图生成一次性 token，120 秒内有效；后台线程定期删除过期 token 及 PNG 文件。
- **定位轨迹采集**：`POST /sensorlog` 将设备定位写入 PostgreSQL，便于地图演示。
- **可配置日志**：优先读取 `log_config.yaml`，缺失时自动回退最小日志配置。支持请求处理时间记录。

## 环境要求

- Python 3.13+
- PostgreSQL 实例（需具备建表权限）
- 推荐 macOS / Linux 环境；Windows 需确认 Matplotlib 字体可用

## 配置

在 `sql_config.yaml` 设置数据库连接与字体路径：

```yaml
postgresql:
  host: 127.0.0.1
  port: 5432
  database: postgres
  username: postgres
  password: your_password

font_path: "fonts/ttf/PingFangSC-Light.ttf"
```

启动时会创建图片令牌表 `image_tokens`；气象数据表在首次上传时按需创建。

## 安装

### 方式一：使用 uv（推荐）

```bash
# 安装 uv
pip install uv

# 同步依赖
uv sync
```

### 方式二：使用 pip

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 启动服务

```bash
# 方式一：直接运行
python main.py

# 方式二：使用 uv
uv run main.py

# 方式三：生产部署（多 workers）
uvicorn main:app --host 0.0.0.0 --port 7763 --workers 2
```

默认监听 `0.0.0.0:7763`。启动时会创建 `data/`、`images/`、`logs/`、`data/sensorlog/` 等目录并加载日志配置。

## API 概览

| 路径 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/api/upload` | POST | 上传气象要素，补算露点和海压，写入 PostgreSQL（按站点 + 日期建表）。 |
| `/api/get/info` | GET | 获取指定站点当日最新观测。 |
| `/api/get/image` | GET | 生成指定站点、日期、要素列表的折线图，返回一次性图片令牌。 |
| `/image` | GET | 消耗一次性图片令牌并返回 PNG。 |
| `/sensorlog` | POST | 接收定位数据并追加到 CSV，供地图演示。 |

### `/api/upload`

- **Body**：`services.config.meteorological_elements` 字段（如 `station_name`、`timestamp`、`temperature`、`pressure`、`relative_humidity`、`wind_speed`、`wind_direction` 等）。
- **处理**：若气温/气压/湿度齐全则补算 `sea_level_pressure`、`dew_point`；UTC 时间写入 `time_utc`。
- **存储**：写入 `{station_name}_{YYYY_MM_DD}`，表不存在会自动创建。

示例：

```bash
curl -X POST http://127.0.0.1:7763/api/upload \
  -H "Content-Type: application/json" \
  -d '{"station_name":"demo","temperature":25.6,"pressure":1013,"relative_humidity":78}'
```

### `/api/get/info`

- **Query**：`station_name`（必填）
- **返回**：当日最新一行记录；若当日表不存在返回 404。

### `/api/get/image`

- **Query**：`station_name`（必填）、`date`（可选，默认当天，格式 `YYYY_MM_DD`）、`elements`
  - `elements` 支持 JSON 数组或逗号分隔字符串；`all` 表示全部允许要素。
- **返回**：`image_id` 与一次性访问 `url`。
- **行为**：图保存在 `images/{uuid}.png`，token 120 秒内有效且单次消费。

### `/image`

- **Query**：`image_token`
- **说明**：验证后立即删除 token，文件由清理线程回收。

### `/sensorlog`

- **Body**：`deviceID`、`locationTimestamp_since1970`、`locationLatitude`、`locationLongitude`、`locationSpeed`、`locationHorizontalAccuracy` 等（额外字段会被忽略）。
- **存储**：写入 PostgreSQL 表 `{deviceID}_{YYYY_MM_DD}`，按天自动分割。

## 数据与图片流程

1. 上传数据写入 PostgreSQL；站点/日期表按需创建。
2. 绘图时从对应表读取指定要素，生成 PNG 并写入 `images/`，令牌信息写入 `image_tokens`。
3. 后台线程每 5 秒检查 `image_tokens`，对超时（>120 秒）的 token 删除数据库记录并移除对应图片。

## 目录结构

```
.
├── sql_config.yaml    # 数据库与字体配置
├── log_config.yaml    # uvicorn 日志配置
├── fonts/             # 中文显示所需字体
├── images/            # 渲染后的折线图（运行时生成并定期清理）
├── data/              # 运行时数据
├── logs/              # 运行日志输出目录
├── routes/            # API 路由（get/post）
├── services/          # 业务层（config、init、plot、sql、utils）
├── main.py            # FastAPI 应用入口
├── pyproject.toml     # 依赖声明
└── uv.lock            # uv 依赖锁定文件
```

## 日志配置

日志配置使用 YAML 格式。优先查找 `log_config.yaml`，找不到则自动生成最小配置。

```yaml
version: 1
disable_existing_loggers: false
formatters:
  colored:
    class: colorlog.ColoredFormatter
    format: "%(log_color)s[%(asctime)s] %(levelname)s%(reset)s - %(message)s"
handlers:
  logconsole:
    class: colorlog.StreamHandler
    formatter: colored
loggers:
  root:
    level: INFO
    handlers: [logconsole]
```

请求处理时间通过 FastAPI 中间件记录，日志格式示例：

```
[2026-02-22 07:06:39] INFO - "POST /api/upload HTTP/1.1" 200 0.012s
```

## 开发与扩展

- 在 `services/elements.py` 的 `ALLOWED_ELEMENTS` / `ELEMENTS` 中扩展可用要素，即可同步影响校验和绘图展示。
- 如需接入其他数据库，可在 `services/sql.py` 中调整 `engine` 创建与表结构。
- 生产部署建议使用容器化，并配置数据库账号最小权限。

## 许可证

MIT License

欢迎通过 Issues / PR 提交改进。
