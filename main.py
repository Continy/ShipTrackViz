from track.trackloader import DataChunk, build_cfg
from track.traj import Trajectory, TrajVizContainer
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
from color.richwarning import *

load_dotenv()
path = Path('./data/新伊敦--数据共享.xlsx').resolve()
llm_cfg = build_cfg('./llm/data.yaml')
llm_cfg.encode = 'GBK'
chunk = DataChunk(path,
                  cfg=llm_cfg,
                  datarange=(0, 100000),
                  force_regeneration=True)
traj = Trajectory(Datachunk=chunk)
# traj.setwinddata('./data/Uruguay.grib', engine='cfgrib')
# sensor_wind_speed = traj['true_wind_speed'] * 0.5144
# w10 = traj['w10']
# w100 = traj['w100']
visualizer = TrajVizContainer(traj, engine='plotly')
visualizer.plot(show=True)
