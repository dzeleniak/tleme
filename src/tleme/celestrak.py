import sys

import httpx
from loguru import logger

from tleme.settings import settings
from tleme.util import days_since_update, get_tle_data_path


def download_sats():
    tle_path = get_tle_data_path()
    try:
        sats = httpx.get(settings.TLE_QUERY_URL)
        with open(tle_path, "w") as f:
            f.write(sats.text)
            logger.success("Successfully initialized catalog.")
    except httpx.HTTPError:
        logger.error("Failed to initialize satellite catalog.")
        sys.exit(1)


def initialize_sats():
    tle_path = get_tle_data_path()
    if tle_path.exists():
        tle_age = days_since_update(tle_path)
        if tle_age > 3:
            logger.info(f"Target file age -> {tle_age:.2f} days.")
            download_sats()

    else:
        logger.info("Target file does not exist. Attempting to initialize.")
        download_sats()
