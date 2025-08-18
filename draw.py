import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time

def draw_last_hour(file_path,target_column, hours_back=24,sep='|',zone='Asia/Shanghai'):
    
    # 读取CSV数据
    df = pd.read_csv(file_path,sep=sep)

    # 转换时间戳为可读格式
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s',utc=True).dt.tz_convert(zone)

    df.sort_values('datetime', inplace=True)

    # 用户输入参数
    target_column = target_column  # 可修改为需要绘制的字段名
    hours_back = hours_back               # 可修改为需要回溯的小时数

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
    
    file_name = f"{target_column}_{hours_back}.png"
    plt.savefig(f"./image/{file_name}")

def draw_specific_day(file_path, target_column, specific_date=None, sep='|', zone='Asia/Shanghai'):

    # 读取CSV数据
    df = pd.read_csv(file_path, sep=sep)

    # 转换时间戳为可读格式并指定时区
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert(zone)
    df.sort_values('datetime', inplace=True)

    # 转换数据类型并处理缺失值
    df[target_column] = pd.to_numeric(df[target_column], errors='coerce')

    # 确定时间范围
    if specific_date:
        # 处理指定日期
        try:
            # 将字符串转换为日期，并设置为指定时区的开始和结束时间
            start_date = pd.to_datetime(specific_date).tz_localize(zone)
            end_date = start_date + timedelta(days=1)
            
            # 筛选该日期的数据
            time_filtered = df[(df['datetime'] >= start_date) & (df['datetime'] < end_date)]
            title_suffix = f"on {specific_date}"
        except Exception as e:
            print(f"日期格式错误: {e}，将使用最近24小时数据")
            specific_date = None  # 出错时使用默认逻辑
    
    # 如果未指定日期或日期格式错误，使用最近24小时数据
    if not specific_date:
        latest_time = df['datetime'].max()
        start_time = latest_time - timedelta(hours=24)
        time_filtered = df[df['datetime'] >= start_time]
        title_suffix = "in Last 24 Hours"

    # 检查数据量并处理
    if len(time_filtered) < 5:  # 如果筛选后数据过少
        print(f"警告：所选时间段数据不足，使用全部数据")
        plot_df = df.copy()
        title_suffix = " (Using All Data)"
    else:
        plot_df = time_filtered.copy()

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
                    label='Missing Values')

    # 设置图表属性
    plt.title(f"{target_column} Trend {title_suffix}")
    plt.xlabel("Time")
    plt.ylabel(target_column)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    # 优化时间轴显示
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    
    # 生成文件名
    if specific_date:
        file_name = f"{target_column}_{specific_date}.png"
    else:
        file_name = f"{target_column}_trend_last24h.png"
    plt.savefig(f"./image/{file_name}")


draw_last_hour("./data/test/esp32 test 2.csv","temperature",2,sep='|',zone='Asia/Shanghai')
#draw_specific_day("./data/test/esp32 test.csv","temperature", specific_date="2025-8-18", sep='|', zone='Asia/Shanghai')