from pathlib import Path
from fastapi import FastAPI
from routers import get,post,oauth
from functions import tools,init
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn
import threading
import sys
import tempfile

app = FastAPI()
app.include_router(get.router)
app.include_router(post.router)
app.include_router(oauth.router)


threading.Thread(target=tools.clean_expired_image_tokens, daemon=True).start()

def setup_log_config():
    """设置日志配置文件"""
    if getattr(sys, 'frozen', False):
        # 打包环境：从临时目录读取配置文件
        base_dir = Path(sys._MEIPASS)
        original_config_path = base_dir / "log_config.ini"
        
        # 将配置文件复制到临时文件（因为uvicorn可能需要写入权限）
        with open(original_config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 创建临时文件
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        temp_config.write(config_content)
        temp_config.close()
        
        return temp_config.name
    else:
        # 开发环境：使用原始文件
        return "./log_config.ini"

if __name__ == "__main__":

    # 初始化日志
    logger = logging.getLogger("uvicorn.app")
    
    # 初始化文件夹
    init.init()
    # 初始化配置文件
    log_config_path = setup_log_config()
    
    # 启动服务端
    app.mount("/image", StaticFiles(directory="image"), name="image")
    uvicorn.run(
        app=app, host="0.0.0.0", port=80, workers=1, log_config=log_config_path
    )
