import os
import time
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from tleme.settings import Settings


def days_since_update(file_path):
    mod_time = os.path.getmtime(file_path)
    time_diff = time.time() - mod_time

    days_diff = time_diff / (24 * 3600)
    return days_diff


@cache
def get_tle_data_path():
    settings = Settings()
    Path(f"{settings.TLE_DATA_DIRECTORY}").mkdir(exist_ok=True, parents=True)
    return Path(f"{settings.TLE_DATA_DIRECTORY}/{settings.TLE_DATA_FILENAME}")


@dataclass
class TLE:
    line0: str
    line1: str
    line2: str
    revolutions_per_day: float


def load_targets() -> dict[str, TLE]:
    lines: str = []
    tle_path = get_tle_data_path()
    with open(tle_path, "r") as f:
        targets = f.read()
        lines = targets.strip().splitlines()

    targets: dict[str, TLE] = {}
    for i in range(0, len(lines), 3):
        l0 = lines[i].strip()
        l1 = lines[i + 1].strip()
        l2 = lines[i + 2].strip()
        catalog_id = l2.split()[1]

        revolutions = float(l2[52:63])

        targets[catalog_id] = TLE(
            line0=l0, line1=l1, line2=l2, revolutions_per_day=revolutions
        )

    return targets
