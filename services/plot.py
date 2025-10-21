from datetime import datetime, timedelta
import matplotlib

# 使用无GUI后端，避免在子线程上创建窗口（macOS 下会崩溃）
matplotlib.use("Agg", force=True)
from matplotlib import dates
from matplotlib.ticker import FuncFormatter
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os
import uuid

logger = logging.getLogger("uvicorn.app")  # 子日志器，继承 uvicorn 的配置

# 将x轴的时间格式化为月-日 时:分
date_format = dates.DateFormatter("%m-%d %H:%M", tz="Asia/Shanghai")

params = [
    ("temperature", "Temperature", "°C", "red"),
    ("pressure", "Pressure", "hPa", "blue"),
    ("relative_humidity", "Relative Humidity", "%", "green"),
    ("wind_speed", "Wind Speed", "m/s", "yellow"),
    ("wind_direction", "Wind Direction", "°", "black"),
    ("ground_temperature", "Ground Temperature", "°C", "orange"),
    ("evaporation_capacity", "Evaporation Capacity", "mm", "indigo"),
    ("sunshine_duration", "Sunshine Duration", "h", "black"),
]


# 映射：列名 -> 参数配置，便于快速筛选
PARAM_MAP = {name: (name, title, unit, color) for name, title, unit, color in params}


def _select_plot_params(columns):
    """根据传入列名筛选参数配置；为空或None则返回全部。"""
    if not columns:
        return params
    return [PARAM_MAP[c] for c in columns if c in PARAM_MAP]


def _read_station_data(station_name, dates_to_read, selected_cols, sep, zone):
    """
    读取站点在指定日期的CSV数据，合并并完成基本清洗/转换。
    - 仅读取需要的列：timestamp + selected_cols
    - 直接将 "NULL" 作为缺失值读取，避免二次替换
    - 转换为带时区的 datetime 并排序
    """
    usecols_allow = set(["timestamp", *selected_cols])
    frames = []
    for day in dates_to_read:
        path = f"./data/{station_name}_{day}.csv"
        if not os.path.exists(path):
            continue
        df = pd.read_csv(
            path,
            sep=sep,
            engine="c",
            memory_map=True,
            na_values=["NULL"],
            usecols=lambda c: c in usecols_allow,
        )
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["timestamp", *selected_cols])

    df = pd.concat(frames, ignore_index=True, sort=False)

    if "timestamp" in df.columns:
        dt = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        df["datetime"] = dt.dt.tz_convert(zone)
        df.sort_values("datetime", inplace=True)

    for col in selected_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _downsample_evenly(df, max_points=1500):
    """大数据量时做简单等间隔降采样，减少绘图点数以提速。"""
    n = len(df)
    if n <= max_points or n == 0:
        return df
    step = max(n // max_points, 1)
    return df.iloc[::step].copy()


def _make_plots(plot_df, plot_params, station_name, title_suffix):
    """统一的绘图函数：使用matplotlib直接绘制以提升速度。"""
    if len(plot_params) == 0:
        raise ValueError("No valid columns to plot.")

    n = len(plot_params)
    fig_h = 5 * n if n > 1 else 9
    fig, axes = plt.subplots(n, 1, figsize=(12, fig_h), sharex=True)
    axes_list = axes if n > 1 else [axes]

    for ax, (column, title, unit, color) in zip(axes_list, plot_params):
        ax.plot(plot_df["datetime"], plot_df[column], color=color, linewidth=1.2)
        ax.set_title(title)
        ax.set_ylabel("")
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos, unit=unit: f"{x:.2f} {unit}")
        )
        ax.grid(alpha=0.7)

    axes_list[-1].set_xlabel("")
    axes_list[-1].xaxis.set_major_formatter(date_format)

    if n > 1:
        fig.suptitle(
            f"Station:{station_name} Multi-element Curve ({title_suffix})",
            fontsize=16,
        )
    else:
        axes_list[0].set_title(
            f"Station:{station_name} {plot_params[0][1]} Curve ({title_suffix})",
            fontsize=16,
        )

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)

    image_id = str(uuid.uuid4())
    file_name = f"{image_id}.png"
    plt.savefig(f"./images/{file_name}", dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"图片'./images/{file_name}'已生成")
    return file_name, image_id


# 绘制自定义小时前的图像
def draw_last_hour_pro(
    station_name, columns=None, hours_back=24, sep="|", zone="Asia/Shanghai"
):
    # 准备读取的日期（今天与昨天）
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    plot_params = _select_plot_params(columns)
    selected_cols = [name for name, *_ in plot_params]

    df = _read_station_data(
        station_name, [yesterday, today], selected_cols, sep=sep, zone=zone
    )

    if df.empty:
        warning = "无可用数据文件"
        logger.warning(warning)
        empty_df = pd.DataFrame({"datetime": [], **{c: [] for c in selected_cols}})
        file_name, image_id = _make_plots(
            empty_df, plot_params, station_name, title_suffix="No Data"
        )
        return file_name, warning, image_id

    # 计算时间范围并筛选
    latest_time = df["datetime"].max()
    start_time = latest_time - timedelta(hours=hours_back)
    time_filtered = df[df["datetime"] >= start_time]
    title_suffix = f"in Last {hours_back} Hours"

    # 判断是否使用全部数据
    filtered_count = len(time_filtered)
    if filtered_count >= 2:
        actual_span = (
            time_filtered["datetime"].max() - time_filtered["datetime"].min()
        ).total_seconds() / 3600
    else:
        actual_span = 0

    use_all_data = False
    warning = ""
    if filtered_count < 5:
        use_all_data = True
        warning = f"数据量不足（{filtered_count}条）"
    elif actual_span < hours_back * 0.9:
        use_all_data = True
        warning = f"时间跨度不足（仅{actual_span:.1f}小时，预期{hours_back}小时）"

    plot_df = df.copy() if use_all_data else time_filtered.copy()
    if use_all_data:
        logger.warning(f"{warning}，使用全部数据")
        title_suffix = "All Available Data"

    # 降采样提速
    plot_df = _downsample_evenly(plot_df)

    file_name, image_id = _make_plots(plot_df, plot_params, station_name, title_suffix)
    return file_name, warning, image_id


# 绘制自定义日期的图像
def draw_specific_day_pro(
    station_name,
    columns=None,
    specific_date=None,
    sep="|",
    zone="Asia/Shanghai",
):
    # 计算目标日期与前一天，优先读取两天数据
    if specific_date is None:
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        today = specific_date
        yesterday = (pd.to_datetime(specific_date) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

    plot_params = _select_plot_params(columns)
    selected_cols = [name for name, *_ in plot_params]

    df = _read_station_data(
        station_name, [yesterday, today], selected_cols, sep=sep, zone=zone
    )

    # 默认使用今天
    if not specific_date:
        specific_date = datetime.now().strftime("%Y-%m-%d")

    warning = ""
    title_suffix = f"on {specific_date}"

    if specific_date:
        try:
            start_date = pd.to_datetime(specific_date).tz_localize(
                zone, ambiguous="NaT", nonexistent="NaT"
            )
            end_date = start_date + timedelta(days=1)

            time_filtered = df[
                (df["datetime"] >= start_date) & (df["datetime"] < end_date)
            ]

            filtered_count = len(time_filtered)
            if filtered_count > 0:
                first_data_time = time_filtered["datetime"].min()
                last_data_time = time_filtered["datetime"].max()
                actual_span = (last_data_time - first_data_time).total_seconds() / 3600
            else:
                actual_span = 0

            use_all_data = False
            if filtered_count == 0:
                use_all_data = True
                warning = f"指定日期{specific_date}无任何数据"
            elif actual_span < 24 * 0.9:
                use_all_data = True
                warning = f"指定日期数据覆盖不足（仅{actual_span:.1f}小时）"
            elif filtered_count < 5:
                use_all_data = True
                warning = f"指定日期数据量过少（仅{filtered_count}条）"

            if use_all_data:
                logger.warning(f"{warning}，将使用全部数据")
                plot_df = df.copy()
                title_suffix = f"{specific_date} Use All Data"
            else:
                plot_df = time_filtered.copy()

        except Exception as e:
            logger.warning(f"日期格式错误: {e}，将使用全部数据")
            plot_df = df.copy()
            title_suffix = "Use All Data"
    else:
        plot_df = df.copy()

    plot_df = _downsample_evenly(plot_df)

    file_name, image_id = _make_plots(plot_df, plot_params, station_name, title_suffix)
    return file_name, warning, image_id


# Test Code
# draw_last_hour_pro("station_2", ["temperature", "pressure", "relative_humidity"], 2)
# draw_specific_day_pro("station_2",["temperature","pressure","relative_humidity"],"2025-08-21")
# draw_specific_day_pro("1",["temperature","pressure","relative_humidity"],"2025-10-12")
