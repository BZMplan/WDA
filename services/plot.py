import matplotlib


# 使用无GUI后端，避免在子线程上创建窗口（macOS 下会崩溃）
matplotlib.use("Agg", force=True)
from matplotlib import dates
from matplotlib.ticker import FuncFormatter
from matplotlib import font_manager
from services.utils import get_table_data
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
def draw(
    station_name, db_name: str = None, table_name: str = None, elements: str = None
):

    plot_elements = _select_plot_elements(elements)
    selected_cols = [name for name, *_ in plot_elements]

    selected_cols.append("time_local")
    # df = _read_station_data(station_name, [date], selected_cols)
    df = get_table_data(db_name, table_name, selected_cols)
    file_name, image_id = _make_plots(df, plot_elements, station_name, "Beta Version")

    return file_name, image_id


d
