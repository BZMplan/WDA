# AGENTS.md

AI助手在本代码库中的工作指南

## 概述

本文档为AI助手在本项目中的工作提供全面的指导原则和规范，确保代码质量、一致性和可维护性。

## 项目概述

### 构建命令

```bash
# 运行 FastAPI 应用程序
python main.py
# 或使用 uv 工具
uv run main.py

# 安装项目依赖
uv sync

# 使用 PyInstaller 打包应用程序（可选）
pyinstaller main.spec
```

### 项目结构

```
wda/
├── main.py                    # FastAPI 应用程序入口点
├── routes/                    # API 路由处理器
│   ├── get.py                # GET 请求处理
│   └── post.py               # POST 请求处理
├── services/                  # 业务逻辑模块
│   ├── config.py             # Pydantic 模型和常量定义
│   ├── postgresql.py         # SQLAlchemy 数据库操作
│   ├── plot.py               # Matplotlib 数据可视化
│   ├── utils.py              # 计算工具函数
│   └── bootstrap.py          # 应用程序初始化和设置
├── web/                      # WebSocket 处理器（可选）
├── static/                   # 静态资源文件
├── config.yaml               # PostgreSQL 和字体配置文件
└── AGENTS.md                 # AI助手工作指南（本文档）
```

## 开发规范

### 代码风格

#### 导入顺序规范

导入语句必须遵循以下顺序：
1. Python 标准库
2. 第三方库
3. 本地项目模块

```python
# 标准库导入
import logging
import time

# 第三方库导入
import pandas as pd
from fastapi import APIRouter

# 本地模块导入
from services import postgresql
```

#### 命名约定

- **变量和函数**: 使用 `snake_case`（小写字母加下划线）
- **Pydantic 模型**: 使用 `snake_case`（遵循现有代码库约定）
- **常量**: 使用 `UPPER_CASE`（全大写加下划线）
- **私有函数/变量**: 使用 `_leading_underscore`（前导下划线）
- **类名**: 使用 `CamelCase`（帕斯卡命名法）

#### 类型提示规范

所有函数必须使用完整的类型提示：

```python
from typing import Dict, List, Any, Optional

def example_function(
    required_param: str,
    optional_param: Optional[int] = None
) -> Dict[str, Any]:
    """
    函数功能描述
    
    参数:
        required_param: 必需参数说明
        optional_param: 可选参数说明
    
    返回:
        返回值说明
    """
    # 函数实现
    return {"key": "value"}
```

#### 错误处理规范

使用结构化的错误处理模式：

```python
from fastapi import status

def handle_database_error():
    try:
        # 数据库操作代码
        result = db.query(...)
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}")
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"数据库错误: {str(e)}",
            "data": None,
        }
    return result
```

#### 日志记录规范

统一使用 Uvicorn 的日志记录器：

```python
import logging

# 始终使用此日志记录器
logger = logging.getLogger("uvicorn.app")

# 日志级别使用指南
logger.info("常规操作信息")      # 正常操作日志
logger.warning("配置问题警告")    # 配置相关问题
logger.error("错误信息")         # 错误情况
logger.debug("调试信息")         # 调试信息（开发时使用）
```

#### 注释规范

1. **中文注释**: 鼓励使用中文注释，提高可读性
2. **复杂函数**: 必须使用中文文档字符串描述算法逻辑
3. **关键代码**: 在复杂算法或业务逻辑处添加解释性注释

#### 数据库操作规范

```python
# SQLAlchemy 2.0 风格查询
from sqlalchemy import select

# 正确的查询方式
stmt = select(User).where(User.name == "张三")
result = session.execute(stmt)

# 表命名规范：table_{站点名称}_{YYYY_MM_DD}
table_name = f"table_{station_name}_{date.strftime('%Y_%m_%d')}"

# 表对象缓存（提高性能）
_TABLE_CACHE = {}
```

### 文档标准

#### 函数文档字符串格式

所有函数必须包含完整的文档字符串：

```python
def calculate_metric(data: List[float], method: str = "average") -> float:
    """
    计算数据集的指定度量值
    
    参数:
        data (List[float]): 输入数据列表
        method (str, optional): 计算方法，可选值为 "average"（平均值）、
                                "median"（中位数）或 "sum"（总和）。
                                默认为 "average"。
    
    返回:
        float: 计算结果
    
    异常:
        ValueError: 当 method 参数无效时抛出
        TypeError: 当 data 包含非数值类型时抛出
    
    注意:
        1. 空列表将返回 0.0
        2. 大数据集建议使用分块计算
        3. 支持并行计算优化（未来版本）
    
    示例:
        >>> calculate_metric([1, 2, 3, 4], "average")
        2.5
    """
    # 函数实现
    pass
```

#### 文档字符串要求清单

1. **函数描述** - 用一句话说明函数主要功能
2. **参数说明** - 每个参数的名称、类型、默认值和含义
3. **返回值** - 返回值的类型和含义
4. **异常说明** - 可能抛出的异常类型和触发条件
5. **注意事项** - 特殊用法、性能考虑、限制条件等
6. **示例** - 简单的使用示例（可选但推荐）

#### 类文档字符串格式

```python
class WeatherData(BaseModel):
    """
    气象数据模型
    
    用于存储和处理单站点的气象观测数据。
    
    属性:
        station_name (str): 气象站点名称
        temperature (float): 温度（摄氏度）
        humidity (float): 相对湿度（百分比）
        pressure (float): 大气压力（百帕）
        timestamp (datetime): 观测时间戳
    
    示例:
        >>> data = WeatherData(
        ...     station_name="北京站",
        ...     temperature=25.5,
        ...     humidity=65.0,
        ...     pressure=1013.25,
        ...     timestamp=datetime.now()
        ... )
    """
    station_name: str
    temperature: float
    humidity: float
    pressure: float
    timestamp: datetime
```

#### 模块文档字符串

每个模块文件应在开头包含模块级别的文档：

```python
"""
plot.py - 气象数据可视化模块

本模块提供气象数据的图表生成功能，包括：
1. 温度-湿度时间序列图
2. 气象要素分布直方图
3. 多站点对比图
4. 气象数据导出为图片文件

主要功能:
- generate_temperature_chart: 生成温度变化图表
- create_humidity_histogram: 创建湿度分布直方图
- export_weather_plot: 导出气象图表到文件

依赖:
- matplotlib>=3.5.0
- pandas>=1.4.0
- numpy>=1.21.0

作者: 气象数据处理团队
版本: 1.0.0
最后更新: 2024年
"""
```

#### 实际示例

**计算函数示例:**

```python
def calculate_dew_point(temperature_c: float, humidity_percent: float) -> float:
    """
    根据温度和湿度计算露点温度
    
    参数:
        temperature_c (float): 气温，单位：摄氏度（℃）
        humidity_percent (float): 相对湿度，单位：百分比（%）
    
    返回:
        float: 露点温度（℃），保留两位小数
    
    计算公式:
        采用 Magnus-Tetens 经验公式：
        Td = (b * α) / (a - α)
        其中 α = (a * T) / (b + T) + ln(RH/100)
        a = 17.27, b = 237.7
    
    适用范围:
        -45℃ ~ 60℃ 的温度范围
    
    参考:
        World Meteorological Organization (WMO) 标准计算方法
    """
    a = 17.27
    b = 237.7
    
    alpha = (a * temperature_c) / (b + temperature_c) + math.log(humidity_percent / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    
    return round(dew_point, 2)
```

**API端点示例:**

```python
@router.get("/api/weather/current")
async def get_current_weather(
    station_name: Optional[str] = Query(None, description="气象站点名称"),
    hours: int = Query(24, description="查询最近多少小时的数据", ge=1, le=168)
) -> Dict[str, Any]:
    """
    获取指定站点的当前气象数据
    
    参数:
        station_name (str, optional): 气象站点名称。如未指定，返回所有站点数据。
        hours (int): 查询最近N小时的数据，范围1-168小时（7天）。
    
    返回:
        Dict[str, Any]: 包含以下结构的响应字典：
            - status (int): HTTP状态码（200表示成功）
            - message (str): 操作结果描述信息
            - data (List[Dict] | None): 气象数据列表，查询失败时为None
            - timestamp (str): 响应生成时间戳
    
    异常响应:
        - 400: 参数验证失败
        - 404: 指定站点不存在
        - 500: 服务器内部错误
    
    示例请求:
        GET /api/weather/current?station_name=北京站&hours=24
    """
    try:
        # 业务逻辑实现
        data = await fetch_weather_data(station_name, hours)
        return {
            "status": status.HTTP_200_OK,
            "message": "数据查询成功",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取气象数据失败: {str(e)}")
        return {
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": f"服务器错误: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }
```

**后台任务示例:**

```python
def cleanup_expired_images():
    """
    清理过期的气象图片文件
    
    后台守护线程函数，定期执行以下任务：
    1. 扫描 image_tokens 数据库表
    2. 识别超过120秒（2分钟）的过期记录
    3. 删除对应的图片文件
    4. 清理数据库中的过期记录
    
    执行频率:
        每5秒执行一次检查
    
    注意:
        1. 此函数包含无限循环，必须在独立线程中运行
        2. 文件删除操作需要适当的错误处理
        3. 数据库操作需要事务保护
        4. 需要考虑并发访问的情况
    
    日志记录:
        - INFO: 正常清理操作
        - WARNING: 文件删除失败但可继续运行
        - ERROR: 数据库连接失败等严重错误
    """
    while True:
        try:
            expired_records = find_expired_image_tokens()
            for record in expired_records:
                delete_image_file(record.file_path)
                delete_database_record(record.id)
            
            if expired_records:
                logger.info(f"清理了 {len(expired_records)} 个过期图片")
            
            time.sleep(5)  # 每5秒检查一次
        except Exception as e:
            logger.error(f"清理任务异常: {str(e)}")
            time.sleep(30)  # 异常后等待30秒再重试
```

## 项目维护指南

### README.md 更新规范

#### 需要更新README的情况

| 变更类型 | 具体场景 | 更新要求 |
|---------|---------|---------|
| **API变更** | 新增/修改/删除API端点 | 更新API文档和示例 |
| | 修改请求/响应参数格式 | 更新参数说明和示例 |
| | 更改API路径或HTTP方法 | 更新路由文档 |
| **配置变更** | 新增或修改配置文件 | 更新配置说明和示例 |
| | 新增环境变量要求 | 添加环境变量说明 |
| | 修改默认配置值 | 更新默认值说明 |
| **依赖变更** | 新增或删除Python包 | 更新依赖列表 |
| | 修改Python版本要求 | 更新版本要求说明 |
| | 新增系统级依赖 | 添加系统依赖说明 |
| **功能变更** | 新增主要功能模块 | 添加功能说明和用法 |
| | 修改数据存储方式 | 更新数据存储说明 |
| | 变更核心业务流程 | 更新架构说明 |
| **结构变更** | 新增或移动目录 | 更新项目结构说明 |
| | 重命名关键文件 | 更新文件说明 |

#### 不需要更新README的情况

1. **内部重构** - 不改变外部接口的代码重构
2. **Bug修复** - 不影响功能使用方式的错误修复
3. **性能优化** - 仅提升性能不影响功能的修改
4. **测试代码** - 测试文件或测试用例的变更
5. **文档改进** - 仅改进现有文档（非API文档）

#### README更新原则

1. **准确性原则** - README内容必须与代码实际行为完全一致
2. **完整性原则** - 新功能必须有完整的使用说明和示例代码
3. **及时性原则** - README更新应与代码变更在同一提交中完成
4. **简洁性原则** - 只记录用户需要知道的信息，隐藏实现细节
5. **一致性原则** - 保持文档风格和格式的一致性

### 版本管理规范

1. **语义化版本** - 遵循 `主版本.次版本.修订号` 格式
2. **变更日志** - 重大变更需在CHANGELOG.md中记录
3. **兼容性** - 次版本更新保持向后兼容性

## 测试配置

### 测试框架

当前项目未配置测试框架，建议按以下方案添加：

```python
# 推荐的测试配置
# 安装测试依赖
# uv add --dev pytest pytest-asyncio pytest-cov httpx

# 测试目录结构建议
# tests/
# ├── conftest.py          # 测试配置和夹具
# ├── test_routes/         # API路由测试
# ├── test_services/       # 业务逻辑测试
# ├── test_integration/    # 集成测试
# └── test_utils/          # 工具函数测试
```

### 测试数据库

- **分离环境**: 测试使用独立的测试数据库
- **数据隔离**: 每个测试用例使用事务回滚保证数据干净
- **性能考虑**: 测试数据库可配置为SQLite内存数据库

### 测试覆盖率目标

- **单元测试**: ≥80% 代码覆盖率
- **集成测试**: 覆盖主要业务流程
- **API测试**: 覆盖所有公开接口

## 部署配置

### 数据库配置

```yaml
# config.yaml 示例
database:
  host: "localhost"
  port: 5432
  name: "weather_data"
  user: "weather_user"
  password: "${DATABASE_PASSWORD}"  # 从环境变量读取
  
fonts:
  chinese: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"  # 中文字体路径
```

### 日志配置

```ini
# log_config.ini 自动生成配置
[loggers]
keys=root,uvicorn

[handlers]
keys=console,file

[formatters]
keys=default

# 详细配置...
```

### 环境变量要求

| 变量名 | 用途 | 示例值 | 是否必需 |
|-------|------|--------|---------|
| DATABASE_PASSWORD | 数据库密码 | secret123 | 是 |
| FONT_PATH | 中文字体路径 | /path/to/font.ttc | 否（有默认值） |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| API_PORT | API服务端口 | 8000 | 否 |

## 依赖管理

### 核心依赖

- **Python**: 3.13+（必须）
- **包管理器**: uv（推荐）或 pip
- **Web框架**: FastAPI 0.104+
- **数据验证**: Pydantic 2.0+
- **数据库**: SQLAlchemy 2.0+ + psycopg2-binary
- **数据可视化**: Matplotlib 3.5+ + pandas 1.4+
- **异步支持**: asyncio + aiohttp（可选）

### 开发依赖

- **代码检查**: black, flake8, mypy
- **测试框架**: pytest, pytest-asyncio, pytest-cov
- **文档生成**: mkdocs, pydoc-markdown
- **性能分析**: py-spy, memory-profiler

### 系统依赖

- **PostgreSQL**: 12+（数据库服务）
- **中文字体**: 文泉驿微米黑或类似字体（图表中文显示）
- **图像处理**: libpng, freetype（图表生成）

## 最佳实践总结

### 代码质量

1. **单一职责** - 每个函数/类只做一件事
2. **明确命名** - 名称应清晰表达意图
3. **错误处理** - 所有可能失败的操作都要有错误处理
4. **类型安全** - 充分利用Python的类型提示
5. **文档完整** - 公共API必须有完整文档

### 性能优化

1. **数据库查询** - 使用适当的索引，避免N+1查询
2. **内存管理** - 大数据集使用分块处理
3. **缓存策略** - 频繁访问的数据适当缓存
4. **异步处理** - I/O密集型操作使用异步

### 安全考虑

1. **SQL注入** - 使用参数化查询，避免字符串拼接
2. **输入验证** - 所有外部输入都要验证和清理
3. **敏感信息** - 密码等敏感信息不写入代码
4. **权限控制** - API端点适当的访问控制

### 维护性

1. **模块化设计** - 功能模块清晰分离
2. **配置外部化** - 配置信息不硬编码
3. **向后兼容** - API变更考虑现有客户端
4. **监控日志** - 关键操作记录详细日志

---

*本文档最后更新: 2024年*
*维护者: 项目开发团队*
*版本: 2.0.0（中文优化版）*