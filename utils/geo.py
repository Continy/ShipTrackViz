import math


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
