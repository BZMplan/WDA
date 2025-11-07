import matplotlib

# 使用无GUI后端，避免在子线程上创建窗口（macOS 下会崩溃）
matplotlib.use("Agg", force=True)
from matplotlib import dates
from matplotlib.ticker import FuncFormatter
from matplotlib import font_manager
import config as cfg
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os
import uuid

logger = logging.getLogger("uvicorn.app")  # 子日志器，继承 uvicorn 的配置

# 设置绘图字体
font_path = "fonts/ttf/PingFangSC-Light.ttf"

font_manager.fontManager.addfont(font_path)
font = font_manager.FontProperties(fname=font_path)

plt.rcParams["font.family"] = font.get_name()
plt.rcParams["axes.unicode_minus"] = False

# 将x轴的时间格式化为月-日 时:分
datetime_format = dates.DateFormatter("%m-%d %H:%M")

# 映射：列名 -> 参数配置，便于快速筛选
ELEMENT_MAP = {
    name: (name, title, unit, color) for name, title, unit, color in cfg.ELEMENTS
}


def _select_plot_elements(plot_elements):
    """根据传入列名筛选参数配置；为空或None则返回全部。"""
    if not plot_elements:
        return cfg.ELEMENTS
    return [ELEMENT_MAP[p] for p in plot_elements if p in ELEMENT_MAP]


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


# 降采样函数
def _downsample_evenly(df, max_points=1500):
    """大数据量时做简单等间隔降采样，减少绘图点数以提速。"""
    n = len(df)
    if n <= max_points or n == 0:
        return df
    step = max(n // max_points, 1)
    return df.iloc[::step].copy()


def _make_plots(plot_df, plot_elements, station_name, title_suffix):
    """统一的绘图函数：使用matplotlib直接绘制以提升速度。"""
    if len(plot_elements) == 0:
        raise ValueError("No valid columns to plot.")
    n = len(plot_elements)
    fig_h = 5 * n if n > 1 else 9
    fig, axes = plt.subplots(n, 1, figsize=(12, fig_h), sharex=True)
    axes_list = axes if n > 1 else [axes]

    for ax, (column, title, unit, color) in zip(axes_list, plot_elements):
        ax.plot(plot_df["time_local"], plot_df[column], color=color, linewidth=1.2)
        ax.set_title(title, fontsize=18)
        ax.set_ylabel("")
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda x, pos, unit=unit: f"{x:.2f} {unit}")
        )
        ax.grid(alpha=0.7)

    axes_list[-1].set_xlabel("")
    axes_list[-1].xaxis.set_major_formatter(datetime_format)

    if n > 1:
        fig.suptitle(
            f"站点:{station_name} Multi-element Curve ({title_suffix})",
            fontsize=24,
        )
    else:
        axes_list[0].set_title(
            f"站点:{station_name} 一日{plot_elements[0][1]} ({title_suffix})",
            fontsize=24,
        )

    plt.tight_layout(rect=[0, 0, 1, 0.985])

    image_id = str(uuid.uuid4())
    file_name = f"{image_id}.png"
    plt.savefig(f"./images/{file_name}", dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"图片'./images/{file_name}'已生成")
    return file_name, image_id


# 绘制图像
def draw(station_name: str, date: str = None, elements: str = None):

    plot_elements = _select_plot_elements(elements)
    selected_cols = [name for name, *_ in plot_elements]

    df = _read_station_data(station_name, [date], selected_cols)

    file_name, image_id = _make_plots(df, plot_elements, station_name, "test")

    return file_name, image_id
