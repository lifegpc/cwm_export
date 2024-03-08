from urllib.parse import urlparse
from os.path import exists, join, dirname
from os import makedirs
from config import Config
import requests


def try_fetch(url):
    for _ in range(5):
        try:
            re = requests.get(url=url)
            if re.status_code == 200:
                return re.content
        except Exception:
            pass
        raise ValueError(f'HTTP ERROR {re.status_code} {re.reason}.')
    raise ValueError('Failed to fetch the image.')


def get_cache(cfg: Config, url: str):
    u = urlparse(url)
    path = u.path
    if path.endswith('/'):
        path = path[:-1]
    path = join(cfg.img_cache_dir, path[1:])
    if exists(path):
        return path
    else:
        img = try_fetch(url)
        d = dirname(path)
        makedirs(d, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(img)
        return path
