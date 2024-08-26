#!/usr/bin/env python3

from riverdata.types import Site, Park


SITES: list[Site] = [
    {
        "site_no": "07099970",
        "name_full": "ARKANSAS RIVER AT MOFFAT STREET AT PUEBLO CO",
        "name_short": "Ark R / Moffat",
        "region": "CO",
        "timezone": "America/Denver",
        "feature_discharge": True,
        "feature_temperature": False,
    },
    {
        "site_no": "09085100",
        "name_full": "COLORADO RIVER BELOW GLENWOOD SPRINGS CO",
        "name_short": "Col R / Glenwood",
        "region": "CO",
        "timezone": "America/Denver",
        "feature_discharge": True,
        "feature_temperature": False,
    },
    {
        "site_no": "09095500",
        "name_full": "COLORADO RIVER NEAR CAMEO CO",
        "name_short": "Col R / Cameo",
        "region": "CO",
        "timezone": "America/Denver",
        "feature_discharge": True,
        "feature_temperature": False,
    },
    {
        "site_no": "09361500",
        "name_full": "ANIMAS RIVER AT DURANGO CO",
        "name_short": "Animas R / Durango",
        "region": "CO",
        "timezone": "America/Denver",
        "feature_discharge": True,
        "feature_temperature": False,
    },
    {
        "site_no": "13206000",
        "name_full": "BOISE RIVER AT GLENWOOD BRIDGE NR BOISE ID",
        "name_short": "Boise R / Glenwood / Boise",
        "region": "ID",
        "timezone": "America/Boise",
        "feature_discharge": True,
        "feature_temperature": False,
    },
]

PARKS: list[Park] = []
