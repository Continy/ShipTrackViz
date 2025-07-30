from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
import os
# 全局变量，用于在启动时加载轨迹数据
trajectory_data = None


def create_app():
    """创建并配置 Flask 应用实例"""
    app = Flask(__name__)

    @app.route('/')
    def index():
        """渲染主可视化页面，并传入 Access Token"""
        # 从环境变量 "CESIUM_ACCESS_TOKEN" 中读取 Token
        cesium_access_token = os.getenv('CESIUM_ACCESS_TOKEN')

        if not cesium_access_token:
            print("Warning: CESIUM_ACCESS_TOKEN environment variable not set.")
            # 可以设置一个备用的公共Token，或者直接在前端处理null值
            cesium_access_token = "YOUR_FALLBACK_PUBLIC_TOKEN_HERE"  # 或者为空字符串 ""

        # 将 Token 传递给模板
        return render_template('index.html', cesium_token=cesium_access_token)

    @app.route('/api/trajectory')
    def get_trajectory_data():
        """提供轨迹数据的 API 接口"""
        if not trajectory_data:
            return jsonify({"error": "Trajectory data not loaded"}), 500

        # 将 Trajectory 对象转换为可序列化的 JSON 格式
        try:
            lats = trajectory_data['latitude']
            lons = trajectory_data['longitude']
            timestamps_pd = pd.to_datetime(trajectory_data['timestamp'])

            other_data = {}
            if trajectory_data.traj_points:
                sample_data = trajectory_data.traj_points[0].data
                keys_to_extract = [
                    k for k, v in sample_data.items()
                    if isinstance(v, (int, float, np.number))
                    and k not in ['latitude', 'longitude']
                ]
                for key in keys_to_extract:
                    try:
                        other_data[key] = trajectory_data[key].tolist()
                    except (KeyError, AttributeError):
                        print(
                            f"Warning: Could not serialize data for key '{key}'. Skipping."
                        )

            # 准备 ECharts 数据
            echarts_timestamps = [
                ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps_pd
            ]
            echarts_series = []
            for key, values in other_data.items():
                # replace all np.nan in values with None for JSON serialization
                values = [None if np.isnan(v) else v for v in values]
                echarts_series.append({
                    "title": key.replace('_', ' ').title(),
                    "data": values
                })
            # 准备 CZML 数据
            start_time_iso = timestamps_pd.min().to_pydatetime().isoformat(
            ) + "Z"
            end_time_iso = timestamps_pd.max().to_pydatetime().isoformat(
            ) + "Z"

            czml = [{
                "id": "document",
                "name": "ShipTrack",
                "version": "1.0",
                "clock": {
                    "interval": f"{start_time_iso}/{end_time_iso}",
                    "currentTime": start_time_iso,
                    "multiplier": 3600  # 调整时钟速度
                }
            }]

            # 路径实体
            czml.append({
                "id": "shipPath",
                "name": "Ship Trajectory",
                "path": {
                    "material": {
                        "solidColor": {
                            "color": {
                                "rgba": [0, 255, 255, 180]
                            }
                        }
                    },
                    "width": 3,
                    "leadTime": 0,
                    "trailTime": 86400 * len(lats),
                    "resolution": 5
                }
            })
            # 点实体

            for i, ts in enumerate(timestamps_pd):
                point_id = f"point_{i}"
                if np.isnan(lons[i]) or np.isnan(lats[i]):
                    print(
                        f"Warning: Skipping point {i} with invalid coordinates."
                    )
                    continue

                point_properties = {
                    'timestamp_iso': ts.to_pydatetime().isoformat() + "Z"
                }
                point_properties['id'] = point_id
                for key in other_data:
                    if np.isnan(other_data[key][i]):
                        continue
                    point_properties[key] = other_data[key][i]

                czml.append({
                    "id": point_id,
                    "name": f"Track Point {i}",
                    "position": {
                        "cartographicDegrees": [lons[i], lats[i], 100]
                    },
                    "properties": point_properties
                })

            czml[1]["position"] = {"reference": "point_0#position"}

            # 将所有数据打包在一个 JSON 对象中返回
            response_data = {
                "czml": czml,
                "echarts": {
                    "timestamps": echarts_timestamps,
                    "series": echarts_series
                }
            }
            return jsonify(response_data)

        except Exception as e:
            print(f"Error serializing data: {e}")
            return jsonify({"error": str(e)}), 500

    return app


def set_trajectory_data(data):
    """全局设置轨迹数据，供 API 使用"""
    global trajectory_data
    trajectory_data = data
