
import logging
import math
import os
import time

logger = logging.getLogger("uvicorn.app")

# 后续将存贮在数据库里
one_time_image_tokens = {}

def clean_expired_image_tokens():

    while True:
        time.sleep(10)  # 每10秒检查一次
        current_time = time.time()
        # 清理120秒（2分钟）前的令牌
        expired_tokens = [
            t
            for t, (created_time, _) in one_time_image_tokens.items()
            if current_time - created_time > 120
        ]
        for image_token in expired_tokens:
            # 删除token和对应的文件
            _, resource_path = one_time_image_tokens[image_token]
            os.remove(os.path.join("images", resource_path))
            # logger.info(f"图片'{os.path.join("images",resource_path)}'过期，已删除")
            img_path = os.path.join("images", resource_path)
            logger.info(f"图片'{img_path}'过期,已删除")
            del one_time_image_tokens[image_token]


def clean_nan_values(data: dict) -> dict:
    """将字典中的NaN值替换为None,确保JSON序列化正常"""
    return {
        key: None if isinstance(value, float) and math.isnan(value) else value
        for key, value in data.items()
    }
