from scipy.stats import spearmanr
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from utils.geo import angle_get
from track.traj import Trajectory


def angular_difference(a, b):
    """计算两个角度 (0-360) 之间的最小差异 (-180 to 180)"""
    diff = (a - b + 180) % 360 - 180
    return diff


# 定义百分比区间和对应颜色
def get_color_by_percentage(data):
    """根据百分比值返回对应颜色"""
    colors = np.full(len(data), '#CCCCCC')  # 默认灰色
    colors[data <= 0.1] = '#00FF00'  # 绿色：<=10%
    colors[(data > 0.1) & (data <= 0.3)] = '#FFFF00'  # 黄色：10%-30%
    colors[(data > 0.3) & (data <= 0.5)] = '#FFA500'  # 橙色：30%-50%
    colors[data > 0.5] = '#FF0000'  # 红色：>50%
    return colors


def get_wind_profile(traj: Trajectory, reverse: bool = False):
    sen_w = traj['true_wind_speed'] * 0.5144
    sen_w_dir = (traj['true_wind_direction'] + 180 * reverse) % 360
    u10 = traj['u10']
    v10 = traj['v10']
    u100 = traj['u100']
    v100 = traj['v100']
    w10 = traj['w10']
    w100 = traj['w100']
    w10_dir = angle_get(u10, v10)
    w100_dir = angle_get(u100, v100)
    return sen_w, sen_w_dir, w10, w100, w10_dir, w100_dir


def plot_series(timedata, dict: dict, route_name: str, type: str):

    plt.figure(figsize=(10, 4))
    for label, series in dict.items():
        plt.plot(timedata, series, label=label)
    plt.xlabel('Time Index')
    plt.ylabel('Wind Speed (m/s)')
    plt.title('Wind Speed Scatter Plot')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'./figure/wind_comparison_{type}_{route_name}.png',
                dpi=300,
                bbox_inches='tight')


def plot_wind_profile(sen_w, w10, w100, sen_w_dir, w10_dir, w100_dir,
                      route_name: str):
    plot_series(np.arange(len(sen_w)), {
        'Sensor Wind Speed': sen_w,
        'W10 Wind Speed': w10,
        'W100 Wind Speed': w100
    },
                route_name,
                type='speed')
    plot_series(np.arange(len(sen_w_dir)), {
        'Sensor Wind Direction': sen_w_dir,
        'W10 Wind Direction': w10_dir,
        'W100 Wind Direction': w100_dir
    },
                route_name,
                type='direction')
    plot_2d_polar_wind_timeseries(
        np.arange(len(sen_w)), {
            'Sensor Wind Direction': sen_w_dir,
            'W10 Wind Direction': w10_dir,
            'W100 Wind Direction': w100_dir
        },
        title='Wind Direction Comparison',
        save_path=f'./figure/wind_direction_comparison_{route_name}.png')


def calculate_percentage_distribution(data):
    """计算各百分比区间的分布"""
    total = len(data)
    p10 = np.sum(data <= 0.1) / total * 100
    p30 = np.sum((data > 0.1) & (data <= 0.3)) / total * 100
    p50 = np.sum((data > 0.3) & (data <= 0.5)) / total * 100
    p_above50 = np.sum(data > 0.5) / total * 100
    return [p10, p30, p50, p_above50]
    # Process each segment


def plot_analyzed_route(sen_w, sen_w_dir, w10, w100, w10_dir, w100_dir,
                        route_name: str):

    slice_sensor_wind = sen_w
    slice_sensor_wind_direction = sen_w_dir
    slice_w10 = w10
    slice_w100 = w100
    slice_w10_dir = w10_dir
    slice_w100_dir = w100_dir

    not_nan_mask = ~np.isnan(slice_sensor_wind) & ~np.isnan(
        slice_w10) & ~np.isnan(slice_w100) & ~np.isnan(
            slice_sensor_wind_direction) & ~np.isnan(
                slice_w10_dir) & ~np.isnan(slice_w100_dir)
    slice_sensor_wind = slice_sensor_wind[not_nan_mask]
    slice_sensor_wind_direction = slice_sensor_wind_direction[not_nan_mask]
    slice_w10 = slice_w10[not_nan_mask]
    slice_w100 = slice_w100[not_nan_mask]
    slice_w10_dir = slice_w10_dir[not_nan_mask]
    slice_w100_dir = slice_w100_dir[not_nan_mask]

    # Calculate Spearman correlation
    s_sensor_w10 = spearmanr(slice_sensor_wind, slice_w10)[0]
    s_sensor_w100 = spearmanr(slice_sensor_wind, slice_w100)[0]
    s_sensor_w10_dir = spearmanr(slice_sensor_wind_direction, slice_w10_dir)[0]
    s_sensor_w100_dir = spearmanr(slice_sensor_wind_direction,
                                  slice_w100_dir)[0]
    s_w10_w100 = spearmanr(slice_w10, slice_w100)[0]
    s_w10_dir_w100_dir = spearmanr(slice_w10_dir, slice_w100_dir)[0]
    print(
        f"Route: {route_name}, "
        f"Sens-W10: {s_sensor_w10:.4f}, Sens-W100: {s_sensor_w100:.4f}, "
        f"Sens-W10 Dir: {s_sensor_w10_dir:.4f}, Sens-W100 Dir: {s_sensor_w100_dir:.4f}, "
        f"W10-W100: {s_w10_w100:.4f}, W10 Dir-W100 Dir: {s_w10_dir_w100_dir:.4f}"
    )
    w10_rme = np.abs(slice_w10 - slice_sensor_wind) / slice_sensor_wind
    w100_rme = np.abs(slice_w100 - slice_sensor_wind) / slice_sensor_wind
    w10_dir_rme = np.abs(
        angular_difference(slice_w10_dir, slice_sensor_wind_direction)) / 180
    w100_dir_rme = np.abs(
        angular_difference(slice_w100_dir, slice_sensor_wind_direction)) / 180
    rmes = {
        'w10_rme': w10_rme,
        'w100_rme': w100_rme,
        'w10_dir_rme': w10_dir_rme,
        'w100_dir_rme': w100_dir_rme
    }

    # 设置更好的图形样式
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")

    # 创建图形：2x3布局（左边4个RME图，右边2个饼图）
    fig = plt.figure(figsize=(24, 14))
    fig.suptitle(f'Wind Data RME Analysis - Route: {route_name}',
                 fontsize=20,
                 fontweight='bold')

    # 数据配置
    data_configs = [
        (w10_rme, 'W10 RME', 'darkred'),
        (w100_rme, 'W100 RME', 'darkgreen'),
        (w10_dir_rme, 'W10 Direction RME', 'darkblue'),
        (w100_dir_rme, 'W100 Direction RME', 'darkorange'),
    ]

    # 绘制RME时间序列图
    for idx, (data, title, main_color) in enumerate(data_configs):
        ax = plt.subplot(2, 3, idx + 1)

        # 获取颜色数组
        colors = get_color_by_percentage(data)

        # 绘制散点图，每个点根据RME值着色
        for j in range(len(data)):
            ax.scatter(j, data[j], c=colors[j], s=20, alpha=0.7)

        # 绘制连线
        ax.plot(data, color=main_color, linewidth=1.5, alpha=0.6)

        # 添加水平参考线
        ax.axhline(y=0.1,
                   color='green',
                   linestyle='--',
                   alpha=0.8,
                   label='10%')
        ax.axhline(y=0.3,
                   color='yellow',
                   linestyle='--',
                   alpha=0.8,
                   label='30%')
        ax.axhline(y=0.5,
                   color='orange',
                   linestyle='--',
                   alpha=0.8,
                   label='50%')

        # 设置图形属性
        ax.set_ylim(0, min(1, np.percentile(data, 95) * 1.1))
        ax.set_title(title, fontsize=16, fontweight='bold', pad=10)
        ax.set_xlabel('Time Index', fontsize=16)
        ax.set_ylabel('RME', fontsize=16)
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.legend(fontsize=16)

        # 添加统计信息文本框
        percentages = calculate_percentage_distribution(data)
        stats_text = (f'≤10%: {percentages[0]:.1f}%\n'
                      f'10-30%: {percentages[1]:.1f}%\n'
                      f'30-50%: {percentages[2]:.1f}%\n'
                      f'>50%: {percentages[3]:.1f}%')
        ax.text(0.02,
                0.98,
                stats_text,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # 绘制风速RME综合饼图
    ax_pie1 = plt.subplot(2, 3, 5)
    wind_speed_data = np.concatenate([rmes['w10_rme'], rmes['w100_rme']])
    wind_speed_percentages = calculate_percentage_distribution(wind_speed_data)

    labels = ['≤10%', '10-30%', '30-50%', '>50%']
    colors_pie = ['#00FF00', '#FFFF00', '#FFA500', '#FF0000']

    wedges, texts, autotexts = ax_pie1.pie(wind_speed_percentages,
                                           labels=labels,
                                           colors=colors_pie,
                                           autopct='%1.1f%%',
                                           startangle=90)
    ax_pie1.set_title('Wind Speed RME Distribution\n(W10 + W100)',
                      fontsize=16,
                      fontweight='bold')

    # 绘制风向RME综合饼图
    ax_pie2 = plt.subplot(2, 3, 6)
    wind_dir_data = np.concatenate([rmes['w10_dir_rme'], rmes['w100_dir_rme']])
    wind_dir_percentages = calculate_percentage_distribution(wind_dir_data)

    wedges, texts, autotexts = ax_pie2.pie(wind_dir_percentages,
                                           labels=labels,
                                           colors=colors_pie,
                                           autopct='%1.1f%%',
                                           startangle=90)
    ax_pie2.set_title('Wind Direction RME Distribution\n(W10 + W100)',
                      fontsize=16,
                      fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'./figure/rme_analysis_{route_name}.png',
                format='png',
                dpi=300,
                bbox_inches='tight')


def plot_2d_polar_wind_timeseries(time_steps,
                                  directions_data: dict,
                                  title="Wind Direction Comparison Over Time",
                                  save_path=None):
    """
    使用2D极坐标图绘制一个或多个风向时间序列。
    半径代表时间，角度代表风向。

    参数:
    time_steps (array-like): 时间步长数组，将作为极坐标的半径。
    directions_data (dict): 一个字典，键为序列名称(str)，值为风向角度数组(array-like, 0-360度)。
                            例如: {'Observed': [d1, d2,...], 'Predicted': [d1, d2,...]}
    title (str): 图表标题。
    save_path (str, optional): 保存图像的文件路径。如果为None，则只显示图像。
    """
    # --- 1. 创建极坐标图形 ---
    # subplot_kw={'projection': 'polar'} 是创建极坐标图的关键
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    fig, ax = plt.subplots(figsize=(12, 12),
                           subplot_kw={'projection': 'polar'})

    # --- 2. 循环绘制每个风向序列 ---
    # 使用预定义的颜色列表来区分不同的序列
    colors = plt.cm.viridis(np.linspace(0, 1, len(directions_data)))

    for i, (name, directions) in enumerate(directions_data.items()):
        # 将风向角度转换为matplotlib极坐标所需的弧度
        # matplotlib的极坐标中，0度在右边（东方），所以我们不需要像3D图中那样转换
        theta_rad = np.deg2rad(directions)

        # 半径r为时间步长
        r = np.array(time_steps)

        # 绘制散点图
        ax.scatter(theta_rad,
                   r,
                   label=name,
                   s=60,
                   alpha=0.7,
                   color=colors[i],
                   zorder=i + 2)

        # 绘制连接线以显示时间演进
        ax.plot(theta_rad, r, alpha=0.5, color=colors[i], zorder=i + 1)

    # --- 3. 美化与标注坐标轴 ---
    # 设置角度（theta）轴，使其像一个罗盘
    ax.set_theta_zero_location('N')  # 将0度（北方）设置在顶部
    ax.set_theta_direction(-1)  # 将角度方向设置为顺时针
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], [
        'N (0°)', 'NE (45°)', 'E (90°)', 'SE (135°)', 'S (180°)', 'SW (225°)',
        'W (270°)', 'NW (315°)'
    ])

    # 设置半径（r）轴
    ax.set_rlabel_position(0)  # 将半径标签放在0度线上
    ax.set_rlim(0, np.max(time_steps) * 1.05)  # 设置半径范围
    ax.set_ylabel("Time Step →", labelpad=30, fontsize=14)  # 半径轴的标签
    ax.yaxis.set_label_position('right')

    # 设置标题和图例
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))

    # 显示网格
    ax.grid(True, linestyle='--', alpha=0.7)

    # --- 4. 保存或显示图像 ---
    if save_path:
        plt.savefig(save_path, format='png', dpi=300, bbox_inches='tight')
