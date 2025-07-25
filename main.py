from track.trackloader import DataInfoExtractor, build_cfg
from track.traj import TrajPoint
import numpy as np
from dotenv import load_dotenv
from pathlib import Path
import warnings

load_dotenv()
path = Path('./data/split.csv').resolve()
llm_cfg = build_cfg('./llm/data.yaml')
llm_cfg.encode = 'utf-8'
data_extractor = DataInfoExtractor(path, cfg=llm_cfg, force_regeneration=True)
