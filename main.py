import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from track.trackloader import DataChunk
from track.traj import Trajectory, TrajVizContainer
from color.richwarning import *

load_dotenv()
path = Path('./data/巴西.csv').resolve()
llm_cfg = './llm/data.yaml'
chunk = DataChunk(
    path,
    cfg=llm_cfg,
    #   datarange=(0, 100000),
    force_regeneration=True,
    encode='GBK')
traj = Trajectory(Datachunk=chunk)
# traj.setwinddata('./data/Uruguay.grib', engine='cfgrib')
# sensor_wind_speed = traj['true_wind_speed'] * 0.5144
# w10 = traj['w10']
# w100 = traj['w100']
visualizer = TrajVizContainer(traj, engine='plotly')
visualizer.plot(show=True)
