#!/usr/bin/env python3

import json

from riverdata.jsonlib import NewJSONEncoder, NewJsonDecoder
from riverdata.sites import PARKS
from riverdata.types import ParkStat, Stats, ParkStats, Park


def write_sites(river_data_filepath: str, stats: Stats):
    with open(river_data_filepath, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2, cls=NewJSONEncoder)
    return True


def read_parks_stats(river_data_filepath: str):
    def _build_park(park: Park, site_stats1: Stats):
        stat_discharge = (
            site_stats1[park["site_no_discharge"]]
            if (park["site_no_discharge"] in site_stats1)
            else None
        )
        stat_temperature = (
            site_stats1[park["site_no_temperature"]]
            if (park["site_no_temperature"] in site_stats1)
            else None
        )
        ret: ParkStat = {
            "park_name": park["name"],
            "park_region": park["region"],
            "park_timezone": park["timezone"],
            "discharge_recent_value": (
                None
                if (stat_discharge is None)
                else stat_discharge["discharge_recent_value"]
            ),
            "discharge_recent_datetime": (
                None
                if (stat_discharge is None)
                else stat_discharge["discharge_recent_datetime"]
            ),
            "discharge_prediction_value": (
                None
                if (stat_discharge is None)
                else stat_discharge["discharge_prediction_value"]
            ),
            "temp_recent_value": (
                None
                if (stat_temperature is None)
                else stat_temperature["temp_recent_value"]
            ),
        }
        return ret

    site_stats: Stats
    with open(river_data_filepath, "r", encoding="utf-8") as fh:
        site_stats = json.load(fh, cls=NewJsonDecoder)
    parks: ParkStats = list(map(lambda p: _build_park(p, site_stats), PARKS))
    return parks
