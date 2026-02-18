# AGENTS.md

Guidelines for AI agents working in this repository.

## Build Commands

```bash
# Run the FastAPI application
python main.py
# or
uv run main.py

# Install dependencies
uv sync

# Package with PyInstaller (optional)
pyinstaller main.spec
```

## Project Structure

- `main.py` - FastAPI application entry point
- `routes/` - API route handlers (get.py, post.py)
- `services/` - Business logic modules
  - `config.py` - Pydantic models and constants
  - `postgresql.py` - Database operations with SQLAlchemy
  - `plot.py` - Matplotlib visualization
  - `utils.py` - Calculation utilities
  - `bootstrap.py` - Initialization and setup
- `web/` - WebSocket handlers (optional)
- `static/` - Static assets
- `config.yaml` - PostgreSQL and font configuration

## Code Style

### Imports

- Order: stdlib → third-party → local modules
- Example:

  ```python
  import logging
  import time

  import pandas as pd
  from fastapi import APIRouter

  from services import postgresql
  ```

### Naming Conventions

- Variables/functions: `snake_case`
- Pydantic models: `snake_case` (following codebase convention)
- Constants: `UPPER_CASE`
- Private functions: `_leading_underscore`

### Type Hints

- Use type hints for function parameters and return types
- Use `Optional[Type]` for nullable values
- Import from `typing` for complex types (Dict, List, Any)

### Error Handling

- Use try/except with specific exception types
- Return structured error responses:

  ```python
  return {
      "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
      "message": f"Error: {str(e)}",
      "data": None,
  }
  ```

### Logging

- Always use: `logger = logging.getLogger("uvicorn.app")`
- Log level: INFO for operations, WARNING for config issues

### Comments

- Chinese comments are acceptable and common
- Document function purpose with docstrings for complex calculations

### Database

- Use SQLAlchemy 2.0 style queries
- Table naming: `table_{station_name}_{YYYY_MM_DD}`
- Cache table objects in `_TABLE_CACHE`

## Documentation Standards

### Function Docstrings

All functions must include comprehensive docstrings following this format:

```python
def function_name(param1: Type, param2: Optional[Type] = None) -> ReturnType:
    """
    函数功能简述

    参数:
        param1 (Type): 参数1的说明
        param2 (Type, optional): 参数2的说明，默认为None

    返回:
        ReturnType: 返回值的说明

    异常:
        ExceptionType: 可能抛出的异常及原因

    注意:
        其他重要信息，如副作用、使用限制等
    """
```

### Docstring Requirements

1. **函数描述**: 用一句话简要说明函数功能
2. **参数说明**: 每个参数必须包含类型和说明
3. **返回值**: 明确返回类型和含义
4. **异常**: 列出可能抛出的异常及触发条件
5. **注意事项**: 特殊用法、副作用、线程安全等

### Class Docstrings

````python
class ClassName(BaseModel):
    """
    类功能描述

    属性:
        attr1 (Type): 属性1说明
        attr2 (Type): 属性2说明

    示例:
        ```python
        obj = ClassName(attr1=value)
        ```
    """
````

### Module Docstrings

每个模块文件应在开头包含模块级别的文档说明（可选，视复杂度而定）。

### Examples

**简单函数:**

```python
def calc_dew_point(temp_c: float, humidity_percent: float) -> float:
    """
    计算露点温度（℃）

    参数:
        temp_c (float): 气温（℃）
        humidity_percent (float): 相对湿度（%）

    返回:
        float: 露点温度（℃），保留两位小数

    公式来源:
        Magnus-Tetens 经验公式（适用于 -45℃ ~ 60℃）
    """
```

**API端点:**

```python
@router.get("/api/get/info")
async def api_get_info(station_name: Optional[str] = None) -> Dict[str, Any]:
    """
    获取实时站点数据

    参数:
        station_name (str, optional): 站点名称

    返回:
        Dict[str, Any]: 包含状态码、消息和数据的字典
        - status: HTTP状态码
        - message: 操作结果消息
        - data: 查询到的数据列表或None
    """
```

**后台任务:**

```python
def clean_expired_image_tokens():
    """
    清理过期的图片

    后台线程函数，每5秒检查一次image_tokens表，
    删除超过120秒的过期图片文件和数据库记录。

    注意:
        此函数包含无限循环，应在后台线程中运行。
    """
```

## README Maintenance

当代码内容有修改时，必须视情况同步更新 README.md：

### 需要更新 README 的情况

1. **API 变更**
   - 新增、修改或删除 API 端点
   - 修改请求/响应参数
   - 更改 API 路径或方法

2. **配置变更**
   - 新增或修改配置文件（config.yaml）
   - 新增环境变量要求
   - 修改默认配置值

3. **依赖变更**
   - 新增或删除依赖包
   - 修改 Python 版本要求
   - 新增系统依赖

4. **功能变更**
   - 新增主要功能模块
   - 修改数据存储方式
   - 变更业务流程

5. **目录结构变更**
   - 新增或移动目录
   - 重命名关键文件

### 不需要更新 README 的情况

- 纯代码重构（不改变功能）
- 修复 bug（不改变使用方式）
- 优化性能
- 添加测试
- 更新文档字符串

### 更新原则

- **准确**: README 必须与实际代码保持一致
- **完整**: 新功能必须有对应的说明和示例
- **及时**: 与代码变更在同一 commit 中更新
- **简洁**: 只记录用户需要知道的信息，不需要实现细节

## Testing

No test framework currently configured. To add tests:

- Consider pytest with pytest-asyncio for async route testing
- Use test database separate from production

## Configuration

- Database config in `config.yaml`
- Font path must be valid for Chinese character rendering
- Log config in `log_config.ini` (auto-generated if missing)

## Dependencies

- Python 3.13+
- uv for package management
- PostgreSQL with psycopg2-binary
- FastAPI, Pydantic, SQLAlchemy, Matplotlib, Pandas
