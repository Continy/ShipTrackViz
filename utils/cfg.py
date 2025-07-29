import yaml
from yacs.config import CfgNode as CN


def build_cfg(yaml_path):

    with open(yaml_path, 'r') as f:
        cfg = CN(yaml.safe_load(f))
    cfg.yamlpath = yaml_path
    return cfg
