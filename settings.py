from pathlib import Path
from config import load_config, save_config

def get_settings():
    path = Path.home()/'.yttranspro.json'
    return load_config(path)

def save_settings(cfg):
    save_config(Path.home()/'.yttranspro.json', cfg)
