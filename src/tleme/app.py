from typing import Optional

import asyncclick as click
import geocoder
import httpx
from loguru import logger
from pyhigh import get_elevation
from rich.console import Console
from rich.table import Table
from skyfield.api import EarthSatellite, load, wgs84

from tleme.util import load_targets


@click.group()
def cli():
    ...


@cli.group()
def get():
    ...


@get.command(name="targets")
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


@get.command(name="visible")
@click.option(
    "--lat", type=Optional[float], help="Latitude of the observer.", default=None
)
@click.option(
    "--lon", type=Optional[float], help="Longitude of the observer.", default=None
)
@click.option(
    "--el",
    type=Optional[float],
    help="Elevation of the observer in meters.",
    default=None,
)
def overhead(lat: Optional[float], lon: Optional[float], el: Optional[float]):
    targets = load_targets()

    if lat is None or lon is None or el is None:
        lat, lon, el = get_location()
    ts = load.timescale()

    table = Table(title="Visible Targets")
    table.add_column("ID", justify="left", style="green")
    table.add_column("NAME", justify="left", style="cyan")
    table.add_column("DAILY REVOLUTIONS", justify="left")

    current_position = wgs84.latlon(lat, lon, el)  # sensor position
    for s_id in targets.keys():  # iterate through all targets
        s = targets[s_id]
        e_sat = EarthSatellite(s.line1, s.line2, name=s.line0)

        difference = e_sat - current_position  # vector from sensor pos to satellite
        e_sat.ts
        alt, az, distance = difference.at(ts.now()).altaz()

        if alt.degrees > 30:
            table.add_row(s_id, s.line0, f"{s.revolutions_per_day:.2f}")

    console = Console()
    console.print(table)


def get_location():
    ip = httpx.get("https://api.ipify.org").content.decode("utf8")
    g = geocoder.ip(ip)

    if g.ok:
        lat, lon = g.latlng
        el = get_elevation(lat, lon)
        return lat, lon, el
    else:
        raise Exception()


@get.command(name="location")
def locate() -> tuple[float, float, float]:
    try:
        lat, lon, el = get_location()
        logger.info(f"Latitude: {lat}")
        logger.info(f"Longitude: {lon}")
        logger.info(f"Elevation: {el}")
    except Exception:
        logger.error("Failed to retrieve location: lat, lon, el")


@get.command(name="tle")
@click.argument("id")
def tle_by_id(id):
    targets = load_targets()
    t = targets[id]

    print(t.line0)
    print(t.line1)
    print(t.line2)
