import logging
import uuid

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import dates, font_manager
from matplotlib.ticker import FuncFormatter

from app.domain.models import ELEMENTS
from app.core.config import load_plot_config
from app.db.sql import get_table_data

logger = logging.getLogger("uvicorn.app")

PLOT_CONFIG = load_plot_config()
font_path = PLOT_CONFIG.get("font_path")
if font_path:
    font_manager.fontManager.addfont(font_path)
font = font_manager.FontProperties(fname=font_path)

matplotlib.use("Agg", force=True)
plt.rcParams["font.family"] = font.get_name()
plt.rcParams["axes.unicode_minus"] = False

datetime_format = dates.DateFormatter("%m-%d %H:%M")

ELEMENT_MAP = {
    name: (name, title, unit, color) for name, title, unit, color in ELEMENTS
}


def _select_plot_elements(plot_elements):
    """
    根据传入列名筛选参数配置

    参数:
        plot_elements: 要绘制的要素列表 (List[str])

    返回:
        List[Tuple]: 筛选后的要素配置列表
    """
    if not plot_elements:
        return ELEMENTS
    return [ELEMENT_MAP[p] for p in plot_elements if p in ELEMENT_MAP]


def _make_plots(plot_df, plot_elements, station_name, title_suffix):
    """
    统一的绘图函数

    参数:
        plot_df (pd.DataFrame): 绘图数据
        plot_elements (List[Tuple]): 要素配置列表
        station_name (str): 站点名称
        title_suffix (str): 标题后缀

    返回:
        Tuple[str, str]: (文件名, 图片ID)

    异常:
        ValueError: 当没有有效的列可绘制时
    """
    if len(plot_elements) == 0:
        raise ValueError("No valid columns to plot.")
    n = len(plot_elements)
    fig_h = 5 * n if n > 1 else 9
    fig, axes = plt.subplots(n, 1, figsize=(12, fig_h), sharex=True)
    axes_list = axes if n > 1 else [axes]

    # plot_df["time_local"] = (
    #     pd.to_datetime(plot_df["time_utc"], utc=True)
    #     .dt.tz_convert("Asia/Shanghai")
    #     .dt.tz_localize(None)
    # )
    plot_df["time_local"] = pd.to_datetime(plot_df["time_utc"]) + pd.Timedelta(hours=8)

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
            f"站点:{station_name} 多要素曲线 ({title_suffix})",
            fontsize=24,
        )
    else:
        axes_list[0].set_title(
            f"站点:{station_name} 一日{plot_elements[0][1]} ({title_suffix})",
            fontsize=24,
        )

    plt.tight_layout(rect=(0, 0, 1, 0.985))

    image_id = str(uuid.uuid4())
    file_name = f"{image_id}.png"
    plt.savefig(f"./images/{file_name}", dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"图片'./images/{file_name}'已生成")
    return file_name, image_id


def setup(station_name, table_name: str, elements=None):
    """
    绘图初始化函数

    参数:
        station_name (str): 站点名称
        table_name (str, optional): 数据表名
        elements (List[str], optional): 要绘制的要素列表

    返回:
        Tuple[str, str]: (文件名, 图片ID)
    """
    plot_elements = _select_plot_elements(elements)
    selected_cols = [name for name, *_ in plot_elements]
    selected_cols.append("time_utc")

    df = get_table_data(table_name, selected_cols)
    file_name, image_id = _make_plots(df, plot_elements, station_name, "Beta Version")

    return file_name, image_id
