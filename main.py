from track.trackloader import DataInfoExtractor, build_cfg
from track.traj import Trajectory, TrajVizContainer
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from color.richwarning import *

load_dotenv()
path = Path('./data/split.csv').resolve()
llm_cfg = build_cfg('./llm/data.yaml')
llm_cfg.encode = 'utf-8'
data_info = DataInfoExtractor(path, cfg=llm_cfg)
traj = Trajectory(DataInfo=data_info)
traj.setenvdata('./data/env.grib', engine='cfgrib')
traj.useEnv()
true_wind_speed = traj['wind']
detected_wind_speed = traj['true_wind_speed']

import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(true_wind_speed, label='True Wind Speed', color='blue')
plt.plot(detected_wind_speed, label='Detected Wind Speed', color='red')
plt.title('True vs Detected Wind Speed')
plt.xlabel('Time')
plt.ylabel('Wind Speed (m/s)')
plt.legend()
plt.grid()
plt.show()
