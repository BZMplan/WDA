import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
def draw(file_path,target_column, hours_back=24,sep='|',zone='Asia/Shanghai'):
    # 读取CSV数据
    df = pd.read_csv(file_path,sep=sep)

    # 转换时间戳为可读格式
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s',utc=True).dt.tz_convert(zone)

    df.sort_values('datetime', inplace=True)

    # 用户输入参数
    target_column = target_column  # 可修改为需要绘制的字段名
    hours_back = 24               # 可修改为需要回溯的小时数

    # 计算时间范围
    latest_time = df['datetime'].max()
    start_time = latest_time - timedelta(hours=hours_back)

    # 筛选数据
    time_filtered = df[df['datetime'] >= start_time]

    # 检查数据量并处理
    if len(time_filtered) < 5:  # 如果筛选后数据过少
        print(f"警告：最近{hours_back}小时数据不足，使用全部数据")
        plot_df = df.copy()
    else:
        plot_df = time_filtered.copy()

    # 转换数据类型并处理缺失值
    plot_df[target_column] = pd.to_numeric(plot_df[target_column], errors='coerce')

    # 创建图表
    plt.figure(figsize=(12, 6))
    plt.plot(plot_df['datetime'], plot_df[target_column], 
            marker='o', linestyle='-', color='b', label=target_column)

    # 标记缺失值
    missing_data = plot_df[plot_df[target_column].isna()]
    if not missing_data.empty:
        plt.scatter(missing_data['datetime'], 
                [plt.ylim()[0]] * len(missing_data),
                color='red', marker='x', s=100, 
                label='None')

    # 设置图表属性
    plt.title(f"{target_column} Trend")
    plt.xlabel("Time")
    plt.ylabel(target_column)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # 优化时间轴显示
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    
    file_name = f"{target_column}_trend.png"
    plt.savefig(file_name)

draw("./data/test/Mplan's Station.csv","temperature",24,sep='|',zone='Asia/Shanghai')
