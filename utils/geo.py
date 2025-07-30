import math
import numpy as np


def displacement_to_latlon(lat, lon, dx, dy):
    '''
    东北方向为正方向，计算位移后的经纬度
    lat: float, 纬度
    lon: float, 经度
    dx: float, 东向位移
    dy: float, 北向位移
    return: tuple, (纬度, 经度)
    >>> displacement_to_latlon(39.9042, 116.4074, 1000, 1000)
    >>> (39.90420000000899, 116.41598600000012)
    '''
    # 地球半径，单位：米
    R = 6371000

    # 将纬度和经度转换为弧度
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    # 计算纬度上的变化
    delta_lat = dy / R
    delta_lat_deg = math.degrees(delta_lat)

    # 计算经度上的变化
    # 需要考虑纬度对经度变化的影响
    delta_lon = dx / (R * math.cos(lat_rad))
    delta_lon_deg = math.degrees(delta_lon)

    # 计算最终的经纬度
    final_lat = lat + delta_lat_deg
    final_lon = lon + delta_lon_deg

    return final_lat, final_lon


def latlon_to_displacement(start_lat, start_lon, end_lat, end_lon):
    # 地球半径，单位：米
    R = 6371000

    # 将经纬度转换为弧度
    start_lat_rad = math.radians(start_lat)
    start_lon_rad = math.radians(start_lon)
    end_lat_rad = math.radians(end_lat)
    end_lon_rad = math.radians(end_lon)

    # 计算纬度和经度的变化量
    delta_lat_rad = end_lat_rad - start_lat_rad
    delta_lon_rad = end_lon_rad - start_lon_rad

    # 计算北向的位移
    dy = delta_lat_rad * R

    # 计算东向的位移，考虑起点纬度
    dx = delta_lon_rad * R * math.cos(start_lat_rad)

    return dx, dy


def angle_get(x, y):
    """
    计算从北方向顺时针方向的角度
    
    参数:
    x : array_like
        x坐标值，正值表示向东方向
    y : array_like  
        y坐标值，正值表示向北方向
        
    返回:
    angle : numpy.ndarray
        从北方向顺时针测量的角度，范围0~360度
        
    注意:
    - 0度表示正北方向
    - 90度表示正东方向  
    - 180度表示正南方向
    - 270度表示正西方向
    """
    # 将输入转换为numpy数组以支持数组运算
    x = np.asarray(x)
    y = np.asarray(y)

    # 使用arctan计算初步角度（以度为单位）
    # 注意：这里使用x/y而不是y/x，因为我们要计算从北方向的角度
    with np.errstate(divide='ignore', invalid='ignore'):
        angle_pre = np.degrees(np.arctan(x / y))

    # 初始化结果数组，与输入数组形状相同
    angle = np.zeros_like(angle_pre)

    # 根据x和y的符号以及angle_pre的符号来确定所在象限，并计算正确的角度

    # 第一象限：x>0, y>0, angle_pre>0
    # 对应地理方位：东北方向，角度范围0-90度
    ind1 = (angle_pre > 0) & (x > 0)
    angle[ind1] = angle_pre[ind1]

    # 第二象限：x>0, y<0, angle_pre<0
    # 对应地理方位：东南方向，角度范围90-180度
    ind2 = (angle_pre < 0) & (x > 0)
    angle[ind2] = angle_pre[ind2] + 180

    # 第三象限：x<0, y<0, angle_pre>0
    # 对应地理方位：西南方向，角度范围180-270度
    ind3 = (angle_pre > 0) & (x < 0)
    angle[ind3] = angle_pre[ind3] + 180

    # 第四象限：x<0, y>0, angle_pre<0
    # 对应地理方位：西北方向，角度范围270-360度
    ind4 = (angle_pre < 0) & (x < 0)
    angle[ind4] = angle_pre[ind4] + 360

    # 特殊情况：x=0, y<0，正南方向
    ind5 = (x == 0) & (y < 0)
    angle[ind5] = 180

    # 处理其他特殊情况
    # x=0, y>0：正北方向，角度为0度（默认值已经是0）
    # x>0, y=0：正东方向，角度为90度
    ind_east = (x > 0) & (y == 0)
    angle[ind_east] = 90

    # x<0, y=0：正西方向，角度为270度
    ind_west = (x < 0) & (y == 0)
    angle[ind_west] = 270

    # x=0, y=0：未定义情况，保持为0

    return angle
