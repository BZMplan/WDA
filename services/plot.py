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
# date_format = dates.DateFormatter("%m-%d %H:%M", tz="Asia/Shanghai")
date_format = dates.DateFormatter("%m-%d %H:%M")

params = [
    ("temperature", "Temperature", "°C", "red"),
    ("pressure", "Pressure", "hPa", "blue"),
    ("relative_humidity", "Relative Humidity", "%", "green"),
    ("dew_point", "Dew Temperature", "°C", "red"),
    ("sea_level_pressure", "Sea Pressure", "hPa", "blue"),
    ("wind_speed", "Wind Speed", "m/s", "yellow"),
    ("wind_direction", "Wind Direction", "°", "black"),
]


# 映射：列名 -> 参数配置，便于快速筛选
PARAM_MAP = {name: (name, title, unit, color) for name, title, unit, color in params}


def _select_plot_params(plot_params):
    """根据传入列名筛选参数配置；为空或None则返回全部。"""
    if not plot_params:
        return params
    return [PARAM_MAP[p] for p in plot_params if p in PARAM_MAP]


def _read_station_data(station_name, dates, selected_cols, sep=","):
    """
    读取站点在指定日期的CSV数据，合并并完成基本清洗/转换。

    健壮性增强：
    - station_name 必须为非空字符串
    - dates_to_read 必须为非空可迭代，且元素可解析为 YYYY-MM-DD
    - 若未读取到任何文件，返回包含 "time_local" 与所需列的空 DataFrame，避免后续 KeyError
    - 仅读取需要的列：time_local + selected_cols
    - 将 "NULL" 作为缺失值读取；转换为带时区的 datetime 并排序
    """
    # 参数校验与归一化
    if not isinstance(station_name, str) or not station_name.strip():
        logger.warning("station_name 非法或为空: %r", station_name)
        return pd.DataFrame({"time_local": [], **{c: [] for c in selected_cols}})

    # if not dates:
    #     logger.warning("dates 为空或未提供: %r", dates)
    #     return pd.DataFrame({"time_local": [], **{c: [] for c in selected_cols}})

    # 过滤非法日期字符串
    valid_days = []
    for d in dates:
        try:
            day = pd.to_datetime(d).strftime("%Y-%m-%d")
            valid_days.append(day)
        except Exception:
            logger.warning("忽略无法解析的日期: %r", d)

    if not valid_days:
        logger.warning("dates 无有效日期: %r", dates)
        return pd.DataFrame({"time_local": [], **{c: [] for c in selected_cols}})

    usecols_allow = set(["time_local", *selected_cols])
    frames = []
    missing = []
    for day in valid_days:
        path = f"./data/{station_name}_{day}.csv"
        if not os.path.exists(path):
            missing.append(path)
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
        if missing:
            logger.warning("未找到任何匹配的数据文件: %s", ", ".join(missing))
        return pd.DataFrame({"time_local": [], **{c: [] for c in selected_cols}})

    df = pd.concat(frames, ignore_index=True, sort=False)

    if "time_local" in df.columns:
        df["time_local"] = pd.to_datetime(df["time_local"], errors="coerce")
        df.sort_values("time_local", inplace=True)
    else:
        # 缺失 time_local 列时，补充 NaT，保持列存在
        df["time_local"] = pd.NaT

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
        ax.plot(plot_df["time_local"], plot_df[column], color=color, linewidth=1.2)
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
def draw_last_hour(
    station_name, columns=None, hours_back=24, sep=",", zone="Asia/Shanghai"
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
        return None, warning, None

    # 计算时间范围并筛选
    latest_time = df["time"].max()
    start_time = latest_time - timedelta(hours=hours_back)
    time_filtered = df[df["time"] >= start_time]
    title_suffix = f"in Last {hours_back} Hours"

    # 统计信息与空数据判断
    filtered_count = len(time_filtered)
    if filtered_count == 0:
        warning = f"指定时间范围内无数据（最近{hours_back}小时）"
        logger.warning(warning)
        return None, warning, None

    if filtered_count >= 2:
        actual_span = (
            time_filtered["time"].max() - time_filtered["time"].min()
        ).total_seconds() / 3600
    else:
        actual_span = 0

    warning = ""

    if filtered_count < 5:
        warning = f"数据量不足（{filtered_count}条）"
        logger.warning(warning)
    elif actual_span < hours_back * 0.9:
        warning = f"时间跨度不足（仅{actual_span:.1f}小时，预期{hours_back}小时）"
        logger.warning(warning)

    plot_df = time_filtered.copy()

    # 降采样提速
    plot_df = _downsample_evenly(plot_df)

    file_name, image_id = _make_plots(plot_df, plot_params, station_name, title_suffix)
    return file_name, warning, image_id


# 绘制自定义日期的图像
def draw_specific_day(
    station_name,
    columns=None,
    specific_date=None,
    sep=",",
    zone="Asia/Shanghai",
):
    # 读取特定日期下的数据数据
    if specific_date is None:
        today = datetime.now().strftime("%Y-%m-%d")
    else:
        today = specific_date

    plot_params = _select_plot_params(columns)
    selected_cols = [name for name, *_ in plot_params]

    df = _read_station_data(station_name, [today], selected_cols, sep=sep, zone=zone)

    # 若未读取到任何数据文件，直接不绘制图像
    if df.empty:
        warning = "无可用数据文件"
        logger.warning(warning)
        return None, warning, None

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

            time_filtered = df[(df["time"] >= start_date) & (df["time"] < end_date)]

            filtered_count = len(time_filtered)
            if filtered_count == 0:
                warning = f"指定日期{specific_date}无任何数据"
                logger.warning(warning)
                return None, warning, None

            first_data_time = time_filtered["time"].min()
            last_data_time = time_filtered["time"].max()
            actual_span = (last_data_time - first_data_time).total_seconds() / 3600

            if actual_span < 24 * 0.9:
                warning = f"指定日期数据覆盖不足（仅{actual_span:.1f}小时）"
                logger.warning(warning)
            elif filtered_count < 5:
                warning = f"指定日期数据量过少（仅{filtered_count}条）"
                logger.warning(warning)

            plot_df = time_filtered.copy()

        except Exception as e:
            logger.warning(f"日期格式错误: {e}，将使用全部数据")
            # 日期错误时无法准确过滤，视为无数据可绘
            return None, f"日期格式错误: {e}", None
    else:
        # 未传 specific_date 的情况下不做强制过滤，保留默认 today 语义
        plot_df = df.copy()

    plot_df = _downsample_evenly(plot_df)

    file_name, image_id = _make_plots(plot_df, plot_params, station_name, title_suffix)
    return file_name, warning, image_id


# 绘制图像
def draw(station_name: str, date: str = None, params: str = None):

    plot_params = _select_plot_params(params)
    selected_cols = [name for name, *_ in plot_params]

    df = _read_station_data(station_name, [date], selected_cols)

    file_name, image_id = _make_plots(df, plot_params, station_name, "test")
    return file_name, image_id
    # # 创建一天完整时间范围（用于固定横轴）
    # start = pd.Timestamp(f"{date} 00:00:00")
    # end = pd.Timestamp(f"{date} 23:59:59")

    # # 绘制散点图
    # plt.figure(figsize=(10, 5))
    # plt.scatter(df["time_local"], df["temperature"], color="tab:blue", label="Temperature")

    # # 设置横轴范围为整天（00:00–23:59）
    # plt.xlim(start, end)

    # # 格式化横轴时间显示
    # plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
    # plt.gca().xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=2))  # 每2小时显示一个刻度
    # plt.gcf().autofmt_xdate()

    # # 标签与标题
    # plt.xlabel("Local Time (UTC+8)")
    # plt.ylabel("Temperature (°C)")
    # plt.title(f"Temperature of {station_name} on {date}")
    # plt.legend()
    # plt.grid(True, linestyle="--", alpha=0.6)
    # plt.tight_layout()
    # plt.show()
