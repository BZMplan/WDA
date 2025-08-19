from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import time
import logging

logger = logging.getLogger("uvicorn.app")  # 子日志器，继承 uvicorn 的配置

def draw_last_hour(file_path, target_column, hours_back, sep='|', zone='Asia/Shanghai'):
    # 读取CSV数据
    df = pd.read_csv(file_path, sep=sep)

    # 转换时间戳为可读格式并指定时区
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True).dt.tz_convert(zone)
    df.sort_values('datetime', inplace=True)

    # 转换数据类型并处理缺失值
    df[target_column] = pd.to_numeric(df[target_column], errors='coerce')

    # 计算时间范围
    latest_time = df['datetime'].max()
    start_time = latest_time - timedelta(hours=hours_back)

    time_filtered = df[df['datetime'] >= start_time]
    title_suffix = f"in Last {hours_back} Hours"

    # 改进的判断逻辑：结合数据量和时间跨度
    filtered_count = len(time_filtered)
    total_count = len(df)

    # 计算筛选数据的实际时间跨度（小时）
    if filtered_count >= 2:  # 至少2条数据才能计算跨度
        actual_span = (time_filtered['datetime'].max() - time_filtered['datetime'].min()).total_seconds() / 3600
    else:
        actual_span = 0

    # 检查条件：数据量足够但时间跨度不足
    use_all_data = False
    if filtered_count < 5:
        use_all_data = True
        warning = f"数据量不足（{filtered_count}条）"
    
    elif actual_span < hours_back * 0.95:
        use_all_data = True
        warning = f"时间跨度不足（仅{actual_span:.1f}小时，预期{hours_back}小时）"
    
    if use_all_data:
        logger.warning(f"{warning}，使用全部数据")
        plot_df = df.copy()
        title_suffix = f"in Last {actual_span:.1f} Hours"
    else:
        plot_df = time_filtered.copy()
    
    # 设置seaborn样式
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6))
    
    if target_column == "temperature":
        uint = "°C"
    elif target_column == "pressure":
        uint = "hPa"
    elif target_column == "relative_humidity":
        uint = "%"
    elif target_column == "wind_speed":
        uint = "m/s"
    elif target_column == "wind_direction":
        uint = "°"
    elif target_column == "ground_temperature":
        uint = "°C"
    elif target_column == "evaporation_capacity":
        uint = "mm"
    elif target_column == "sunshine_duration":
        uint = "h" 
    else:
        uint = ""
        
    # 使用seaborn绘制线图
    sns.lineplot(   
        data=plot_df,
        x='datetime',
        y=target_column,
        label=target_column,
    )
    
    # 标记缺失值
    missing_data = plot_df[plot_df[target_column].isna()]
    if not missing_data.empty:
        plt.scatter(
            missing_data['datetime'],
            [plt.ylim()[0]] * len(missing_data),
            color='red',
            marker='x',
            s=100,
            label='Missing value'
        )
    
    # 设置图表属性
    plt.title(f"{target_column} Curve ({title_suffix})", fontsize=14)
    plt.xlabel("Time", fontsize=12)
    plt.ylabel(f"{target_column} ({uint})", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 优化时间轴显示
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    
    # 保存图片
    file_name = f"{target_column}_last_{actual_span:.1f}.png"
    plt.savefig(f"./image/{file_name}", dpi=300, bbox_inches='tight')
    plt.close()
    
    return file_name

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
            # 确保日期转换正确处理时区，避免跨天问题
            start_date = pd.to_datetime(specific_date).tz_localize(zone, ambiguous='NaT', nonexistent='NaT')
            end_date = start_date + timedelta(days=1)
            
            # 筛选该日期的全部数据（当天00:00至23:59:59）
            time_filtered = df[(df['datetime'] >= start_date) & (df['datetime'] < end_date)]
            title_suffix = f"on {specific_date}"
            
            # 验证是否为当天完整数据
            filtered_count = len(time_filtered)
            
            # 计算当天实际有数据的时间范围
            if filtered_count > 0:
                first_data_time = time_filtered['datetime'].min()
                last_data_time = time_filtered['datetime'].max()
                actual_coverage = (last_data_time - first_data_time).total_seconds() / 3600  # 小时
            else:
                actual_coverage = 0
            
            # 判断是否使用全部数据的条件
            use_all_data = False
            warning = ""
            
            if filtered_count == 0:
                use_all_data = True
                warning = f"指定日期{specific_date}无任何数据"
            elif actual_coverage < 24 *0.9:
                use_all_data = True
                warning = f"指定日期数据覆盖不足（仅{actual_coverage:.1f}小时）"
            elif filtered_count < 5:
                use_all_data = True
                warning = f"指定日期数据量过少（仅{filtered_count}条）"
            
            if use_all_data:
                logger.warning(f"{warning}，将使用全部数据")
                plot_df = time_filtered.copy()
                title_suffix = f"{specific_date} Using All Data"
            
            
        except Exception as e:
            logger.warning(f"日期格式错误: {e}，将使用最近24小时数据")
            specific_date = None  # 出错时使用默认逻辑
    
    # 如果未指定日期或日期格式错误，使用最近24小时数据
    if not specific_date:
        latest_time = df['datetime'].max()
        start_time = latest_time - timedelta(hours=24)
        
        time_filtered = df[df['datetime'] >= start_time]
        title_suffix = "in Last 24 Hours"
        
        # 改进的判断逻辑：结合数据量和时间跨度
        filtered_count = len(time_filtered)
        total_count = len(df)

        # 计算筛选数据的实际时间跨度（小时）
        if filtered_count >= 2:  # 至少2条数据才能计算跨度
            actual_span = (time_filtered['datetime'].max() - time_filtered['datetime'].min()).total_seconds() / 3600
        else:
            actual_span = 0

        # 检查条件：数据量足够但时间跨度不足
        use_all_data = False
        if filtered_count < 5:
            use_all_data = True
            warning = f"数据量不足（{filtered_count}条）"
        elif actual_span < 24 * 0.9:
            use_all_data = True
            warning = f"时间跨度不足（仅{actual_span:.1f}小时，预期24小时）"

        if use_all_data:
            logger.warning(f"{warning}，使用全部数据")
            plot_df = df.copy()
            title_suffix = "Using All Data"
        else:
            plot_df = time_filtered.copy()

    # 设置seaborn样式
    sns.set_style("whitegrid")
    plt.figure(figsize=(12, 6))
    
    if target_column == "temperature":
        uint = "°C"
    elif target_column == "pressure":
        uint = "hPa"
    elif target_column == "relative_humidity":
        uint = "%"
    elif target_column == "wind_speed":
        uint = "m/s"
    elif target_column == "wind_direction":
        uint = "°"
    elif target_column == "ground_temperature":
        uint = "°C"
    elif target_column == "evaporation_capacity":
        uint = "mm"
    elif target_column == "sunshine_duration":
        uint = "h" 
    else:
        uint = ""
    
    # 使用seaborn绘制曲线
    sns.lineplot(
        data=plot_df,
        x='datetime',
        y=target_column,
        label=target_column
    )

    # 标记缺失值
    missing_data = plot_df[plot_df[target_column].isna()]
    if not missing_data.empty:
        plt.scatter(
            missing_data['datetime'], 
            [plt.ylim()[0]] * len(missing_data),
            color='red', 
            marker='x', 
            s=100, 
            label='Missing Values'
            
        )

    # 设置图表属性
    plt.title(f"{target_column} curve ({title_suffix})", fontsize=14)
    plt.xlabel("Time", fontsize=12)
    plt.ylabel(f"{target_column} ({uint})", fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 优化时间轴显示
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    
    # 生成文件名
    if specific_date:
        file_name = f"{target_column}_{specific_date}.png"
    else:
        file_name = f"{target_column}_24.png"
    plt.savefig(f"./image/{file_name}")
    plt.close() 
    
    return file_name
