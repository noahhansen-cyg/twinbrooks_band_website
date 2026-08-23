import os
import yaml

_DATA_DIR = os.path.dirname(__file__)

FILES = {
    "band": "band.yaml",
    "members": "members.yaml",
    "shows": "shows.yaml",
    "videos": "videos.yaml",
    "services": "services.yaml",
    "differentiators": "differentiators.yaml",
    "links": "links.yaml",
}


def _load(filename):
    path = os.path.join(_DATA_DIR, filename)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_all():
    return {key: _load(filename) for key, filename in FILES.items()}
