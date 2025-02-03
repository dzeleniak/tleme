import os
import sys
import time
from dataclasses import dataclass

import asyncclick as click
import httpx
from loguru import logger
from rich.console import Console
from rich.table import Table
from skyfield.api import EarthSatellite, load, wgs84

tle_query_url = "https://celestrak.org/NORAD/elements/gp.php?FORMAT=tle&GROUP=ACTIVE"
tle_data_path = "data/satellites.tle"


def days_since_update(file_path):
    # Get the modification time of the file
    mod_time = os.path.getmtime(file_path)
    # Calculate the time difference from now in seconds
    time_diff = time.time() - mod_time
    # Convert seconds to days
    days_diff = time_diff / (24 * 3600)
    return days_diff


def download_sats():
    try:
        sats = httpx.get(tle_query_url)
        with open(tle_data_path, "w") as f:
            f.write(sats.text)
            logger.success("Successfully initialized catalog.")
    except httpx.HTTPError:
        logger.error("Failed to initialize satellite catalog.")
        sys.exit(1)


def initialize_sats():
    if os.path.exists(tle_data_path):
        tle_age = days_since_update(tle_data_path)
        if tle_age > 3:
            logger.info(f"Target file age -> {tle_age:.2f} days.")
            download_sats()

    else:
        logger.info("Target file does not exist. Attempting to initialize.")
        download_sats()


@dataclass
class TLE:
    line0: str
    line1: str
    line2: str
    revolutions_per_day: float


def load_targets() -> dict[str, TLE]:
    lines: str = []
    with open(tle_data_path, "r") as f:
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


@click.group()
def cli():
    ...


@cli.command(name="all")
def all_targets():
    targets = load_targets()

    table = Table(title="Targets")
    table.add_column("ID", justify="left", style="green")
    table.add_column("NAME", justify="left", style="cyan")
    table.add_column("DAILY REVOLUTIONS", justify="left")
    for t in targets.keys():
        table.add_row(t, targets[t].line0, f"{targets[t].revolutions_per_day:.2f}")

    console = Console()
    console.print(table)


@cli.command(name="visible")
@click.option("--lat", type=float, help="Latitude of the observer.")
@click.option("--lon", type=float, help="Longitude of the observer.")
@click.option("--el", type=float, help="Elevation of the observer in meters.")
def overhead(lat: float, lon: float, el: float):
    ts = load.timescale()
    sats = load_targets()

    table = Table(title="Visible Targets")
    table.add_column("ID", justify="left", style="green")
    table.add_column("NAME", justify="left", style="cyan")
    table.add_column("DAILY REVOLUTIONS", justify="left")

    current_position = wgs84.latlon(lat, lon, el)  # sensor position
    for s_id in sats.keys():  # iterate through all targets
        s = sats[s_id]
        e_sat = EarthSatellite(s.line1, s.line2, name=s.line0)

        difference = e_sat - current_position  # vector from sensor pos to satellite

        alt, az, distance = difference.at(ts.now()).altaz()

        if alt.degrees > 40:
            table.add_row(s_id, s.line0, f"{s.revolutions_per_day:.2f}")

    console = Console()
    console.print(table)


@cli.command(name="id")
@click.argument("id")
def tle_by_id(id):
    targets = load_targets()
    t = targets[id]

    print(t.line0)
    print(t.line1)
    print(t.line2)
