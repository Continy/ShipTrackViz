import numpy as np
from pathlib import Path
from functools import partial
from dotenv import load_dotenv
from track.trackloader import DataChunk
from track.traj import Trajectory, TrajVizContainer
from color.richwarning import *
from utils.geo import angle_get

load_dotenv()
path = Path('./data/巴西.csv').resolve()
llm_cfg = './llm/data.yaml'


def validclipper(data: np.ndarray, range: tuple = (0, 20000)) -> np.ndarray:
    """
    data in [x_min, x_max] will be clipped to NaN
    :param x: Input data array.
    :return: Clipped data array.
    """
    return np.where((data < range[0]) | (data > range[1]), np.nan, data)


chunk = DataChunk(path,
                  cfg=llm_cfg,
                  datarange=(43641, 47000),
                  force_regeneration=True,
                  encode='GBK',
                  clip={
                      'SFOC': partial(validclipper, range=(0, 10000)),
                      'fuel_consumption': partial(validclipper,
                                                  range=(0, 20000)),
                  })
traj = Trajectory(Datachunk=chunk)
traj.setwinddata('./data/brazil.grib', engine='cfgrib')
sensor_wind = traj['true_wind_speed'] * 0.5144
sensor_wind_direction = traj['true_wind_direction']
sensor_wind_direction = (sensor_wind_direction + 180) % 360
u10 = traj['u10']
v10 = traj['v10']
u100 = traj['u100']
v100 = traj['v100']
w10 = traj['w10']
w100 = traj['w100']
w10_dir = angle_get(u10, v10)
w100_dir = angle_get(u100, v100)
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(sensor_wind, label='Sensor Wind Speed (m/s)')
plt.plot(w10, label='10m Wind Speed (m/s)')
plt.plot(w100, label='100m Wind Speed (m/s)')
plt.title('Wind Speed Comparison')
plt.xlabel('Time')
plt.ylabel('Wind Speed (m/s)')
plt.legend()
plt.subplot(2, 1, 2)
plt.plot(sensor_wind_direction, label='Sensor Wind Direction (degrees)')
plt.plot(w10_dir, label='10m Wind Direction (degrees)')
plt.plot(w100_dir, label='100m Wind Direction (degrees)')
plt.title('Wind Direction Comparison')
plt.xlabel('Time')
plt.ylabel('Wind Direction (degrees)')
plt.legend()
plt.tight_layout()
plt.show()

visualizer = TrajVizContainer(traj, engine='webgl')
visualizer.launch_web_app(port=8000, debug=False)
