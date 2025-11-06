# Weather Data Analyzer & Visualization

一个基于 **FastAPI** 的气象站数据上传、查询与可视化服务。系统接收站点分钟级观测值，自动完成基础气象指标计算、CSV 存储、折线图渲染，并通过一次性令牌安全地暴露图像资源。

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/BZMplan/WDA)
---

## 核心特性

- **数据采集**：`POST /api/upload` 支持多种气象要素（气温、气压、湿度、风向风速等），自动合并同一分钟数据并保留两位小数。
- **智能补充指标**：根据上传数据计算海平面气压与露点温度，减少终端侧计算负担。
- **快速查询**：`GET /api/get/info` 可按站点+时间获取最近数据，并返回全部可绘制气象要素。
- **图像服务**：`GET /api/get/image` 生成多要素折线图，图片以 UUID 命名，使用一次性 token 在 120 秒内访问。
- **自清理机制**：后台线程定期回收过期 token 及对应图片，确保存储目录纤细可控。
- **模块化设计**：`routes/` 管理 API，`services/` 负责绘图、初始化、工具函数，便于扩展。

---

## 快速开始

### 环境准备

- Python 3.13+
- 推荐 macOS / Linux 环境（Windows 需确保 Matplotlib 字体正常）
- 字体文件 `fonts/ttf/PingFangSC-Light.ttf` 已随仓库提供，用于中文标注

### 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install fastapi[standard] pandas matplotlib seaborn uvicorn colorlog python-multipart pyinstaller
```

> 可选：安装 `uv` 后运行 `uv sync` ，将依据 `pyproject.toml` 安装全部依赖。

### 启动服务

```bash
python main.py
# 或使用 uv
uv run main.py
```

默认监听 `0.0.0.0:7763`。首次启动会自动创建 `data/`, `images/`, `logs/` 等目录，并加载自定义日志配置。

### 健康检查

```bash
curl -X POST http://127.0.0.1:7763/api/upload \
  -H "Content-Type: application/json" \
  -d '{"station_name":"demo","temperature":25.6,"pressure":1013,"relative_humidity":78}'
```

成功后可以访问 `http://127.0.0.1:7763/docs` 查看自动生成的 Swagger 文档。

---

## API 概览

| 路径 | 方法 | 说明 |
| ---- | ---- | ---- |
| `/api/upload` | POST | 上传单条观测数据；自动聚合同一分钟内的记录，输出结构化 CSV。 |
| `/api/get/info` | GET | 查询指定站点在某一时刻（或最近一次）的观测值集合。 |
| `/api/get/image` | GET | 生成指定站点、日期、要素列表的折线图，返回一次性图片令牌。 |
| `/image` | GET | 消耗一次性图片令牌并返回 PNG 文件。 |

### `/api/upload`

- **Body**：`config.meteorological_elements` 字段（JSON）
- **自动处理**：
  - 根据 `timestamp` 生成本地/UTC 时间列
  - 计算 `sea_level_pressure` 与 `dew_point`
  - 写入 `data/{station}_{YYYY-MM-DD}.csv`
  - 暂存于 `data/tmp.csv` 用于分钟级聚合

### `/api/get/info`

- **Query**：`station_name`（必填）、`time_local`（可选）
- **返回**：`status`、`message`、`data`，其中 `data` 包含所有可绘制要素及时间戳
- **要素筛选**：内部使用 `services.plot._select_plot_elements`，确保字段合法

### `/api/get/image`

- **Query**：`station_name`、`date`（默认今天）、`elements`
  - `elements` 支持 JSON 数组或逗号分隔字符串，例如 `["temperature","pressure"]` 或 `temperature,pressure`
  - `all` 表示绘制所有允许要素
- **返回**：`image_id` 和一次性访问 `url`
- **图像行为**：
  - Matplotlib 后端使用 `Agg`，适配无头环境
  - 输出文件位于 `images/{uuid}.png`
  - 令牌 120 秒内有效，消费或过期后自动删除

---

## 数据与图像处理流程

1. **写入**：上传数据首先进入 `data/tmp.csv`，系统以站点+分钟为粒度聚合后写入目标 CSV。
2. **读取**：绘图时按日期读取 `data/{station}_{YYYY-MM-DD}.csv`，自动过滤缺失列并进行类型转换。
3. **降采样**：可根据需要引入 `services.plot._downsample_evenly` 做等距抽样，避免大数据量导致绘图变慢。
4. **绘图**：每个要素独立子图，Y 轴单位由配置驱动，X 轴使用 `%m-%d %H:%M` 格式。
5. **清理**：`services.utils.clean_expired_image_tokens` 线程每 10 秒扫描一次，删除超时图片及令牌。

---

## 目录结构

```
.
├── data/               # 站点数据 CSV（运行时生成）
├── fonts/              # 中文显示所需字体
├── images/             # 渲染后的折线图（运行时生成并定期清理）
├── logs/               # 运行日志输出目录
├── routes/             # FastAPI 路由定义
│   ├── get.py          # 查询类接口
│   └── post.py         # 上传接口
├── services/           # 业务服务层
│   ├── bootstrap.py    # 目录创建与日志配置加载
│   ├── plot.py         # 数据读取与 Matplotlib 绘图
│   └── utils.py        # 令牌缓存与数据清洗工具
├── config.py           # Pydantic 模型与要素配置
├── log_config.ini      # uvicorn 日志配置
├── main.py             # FastAPI 应用入口
├── pyproject.toml      # 项目依赖声明
└── README.md
```

---

## 日志与监控

- 默认日志记录到标准输出，也可根据 `log_config.ini` 写入文件。
- 关键事件（图像生成、令牌清理）通过 `uvicorn.app` 日志器输出。
- 若未找到 `log_config.ini`，将退回最小化日志配置并写入临时文件。

---

## 开发建议

- **元素扩展**：在 `config.ELEMENTS` 中追加待绘制要素即可同步影响上传校验与绘图标题。
- **持久化**：当前使用 CSV 储存，可替换为数据库并在 `services.plot._read_station_data` 中调整读取逻辑。
- **安全加固**：可在 FastAPI 中引入 OAuth2/JWT，对上传与查询接口增加鉴权。
- **部署**：生产环境建议通过 `uvicorn main:app --host 0.0.0.0 --port 7763 --workers 2` 或使用容器化方案。

---

## 许可证 & 贡献

- 许可证：MIT License
- 欢迎通过 Issues / Pull Requests 反馈问题或提交改进建议。
