#!/usr/bin/env python3

from typing import TypedDict, cast
from io import StringIO
import csv
import datetime
import zoneinfo
from decimal import Decimal
import re
from pprint import pprint

import requests

from riverdata.sites import SITES
from riverdata.types import Stat, Stats, Site
from riverdata.math import get_prediction_info


class FetchResult(TypedDict):
    text: str
    url: str


class NormRowBase(TypedDict):
    site: str
    agency: str
    datetime: datetime.datetime
    timezone: str


class NormRowDischarge(NormRowBase):
    discharge: Decimal | None


class NormRowTemperature(NormRowBase):
    temperature: Decimal | None


class NormRow(NormRowDischarge, NormRowTemperature):
    discharge: Decimal | None
    temperature: Decimal | None


class OrigRow(TypedDict):
    agency: str
    site_no: str
    datetime: str
    timezone: str
    discharge: str | None
    discharge_provisional: str | None
    temperature: str | None
    temperature_provisional: str | None


class StatDischarge(TypedDict):
    recent_value: Decimal
    recent_datetime: datetime.datetime
    prediction_value: Decimal
    prediction_direction: int
    high_value: Decimal
    low_value: Decimal
    high_datetime: datetime.datetime
    low_datetime: datetime.datetime


class StatTemp(TypedDict):
    recent_value: Decimal
    recent_datetime: datetime.datetime
    prediction_value: Decimal
    prediction_direction: int
    high_value: Decimal
    low_value: Decimal
    high_datetime: datetime.datetime
    low_datetime: datetime.datetime


class DocParts(TypedDict):
    headers: list[str]
    data: str


PREDICTION_COUNT = 8

URL = "https://waterdata.usgs.gov/nwis/uv"

DATA_FIELDS: list[tuple[str, str]] = [
    (r"^agency_cd$", "agency"),
    (r"^site_no$", "site_no"),
    (r"^datetime$", "datetime"),
    (r"^tz_cd$", "timezone"),
    (r"^\d+_00060$", "discharge"),
    (r"^\d+_00060_cd$", "discharge_provisional"),
    (r"^\d+_00010$", "temperature"),
    (r"^\d+_00010_cd$", "temperature_provisional"),
]

TZ_FIXES = {
    "HDT": "Pacific/Honolulu",
    "AKDT": "America/Anchorage",
    "AKST": "America/Anchorage",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "MDT": "America/Denver",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "EDT": "America/New_York",
}


def _build_url_params(site_no: str, begin_dt: datetime.date):
    return {
        "cb_00010": "on",
        "cb_00060": "on",
        "format": "rdb",
        "site_no": site_no,
        "period": "",
        "begin_date": begin_dt.isoformat(),
    }


def _fetch(site: Site, begin_date: datetime.date):
    params = _build_url_params(site["site_no"], begin_date)
    resp = requests.get(URL, params=params)
    return cast(FetchResult, {"text": resp.text, "url": resp.url})


def _cleanup(text: str):
    lines1 = text.splitlines()
    lines2 = list(filter(lambda x: not x.startswith("#"), lines1))
    if len(lines2) == 0:
        return None
    line_h = _transform_csv_headers(lines2[0].split("\t"))
    lines3 = list(filter(lambda x: x[0] > 1, enumerate(lines2)))
    lines4 = list(map(lambda x: x[1], lines3))
    clean = "\n".join(lines4)
    ret: DocParts = {"headers": line_h, "data": clean}
    return ret


def _transform_csv_headers(headers: list[str]):
    def _transform(header: str):
        for pat, name in DATA_FIELDS:
            if re.match(pat, header):
                return name
        return header

    return list(map(_transform, headers))


def _to_csv(doc: DocParts):
    fh = StringIO(doc["data"])
    reader = csv.DictReader(fh, doc["headers"], delimiter="\t")
    revrows = list(reversed(list(reader)))
    outrows = cast(list[OrigRow], revrows)
    return outrows


def _get_tz(tzname1: str, tzname2: str):
    def _find(tz: str):
        try:
            return zoneinfo.ZoneInfo(tz)
        except zoneinfo.ZoneInfoNotFoundError:
            pass
        return None

    tzobj1 = _find(tzname1)
    if tzobj1 is not None:
        return tzobj1
    tzobj2 = _find(tzname2)
    if tzobj2 is not None:
        return tzobj2
    tzname3 = TZ_FIXES[tzname1] if tzname1 in TZ_FIXES else None
    if tzname3 is not None:
        tzobj3 = _find(tzname3)
        if tzobj3 is not None:
            return tzobj3
    tzobj4 = _get_tz_utc()
    return tzobj4


def _get_tz_utc():
    return zoneinfo.ZoneInfo("UTC")


def _make_date(dtstr: str, tzstr: str, fallback_tzstr: str):
    tzinfo = _get_tz(tzstr, fallback_tzstr)
    loc_dt = datetime.datetime.fromisoformat(dtstr).replace(tzinfo=tzinfo)
    utc_dt = loc_dt.astimezone(_get_tz_utc())
    return utc_dt


def _normalize_doc(site: Site, rows: list[OrigRow]):
    def _build(x: OrigRow) -> NormRow:
        return {
            "agency": x["agency"],
            "datetime": _make_date(x["datetime"], x["timezone"], site["timezone"]),
            "timezone": site["timezone"],
            "discharge": (
                _make_decimal_from_str(x["discharge"])
                if (
                    ("discharge" in x)
                    and (x["discharge"] != "")
                    and (x["discharge"] is not None)
                )
                else None
            ),
            "temperature": (
                _make_decimal_from_str(x["temperature"])
                if (
                    ("temperature" in x)
                    and (x["temperature"] != "")
                    and (x["temperature"] is not None)
                )
                else None
            ),
            "site_no": x["site_no"],
        }

    return list(map(_build, rows))


def _make_decimal_from_str(val: str):
    return Decimal(val).quantize(Decimal(".00"))


def _get_recent_discharges(rows: list[NormRowDischarge]):
    rec_rows = list(reversed(rows[:PREDICTION_COUNT]))
    return list(map(lambda x: float(x["discharge"]), rec_rows))


def _get_recent_temps(rows: list[NormRowTemperature]):
    rec_rows = list(reversed(rows[:PREDICTION_COUNT]))
    return list(map(lambda x: float(x["temperature"]), rec_rows))


def _get_discharge_high_row(rows: list[NormRowDischarge]):
    if len(rows) == 0:
        return None
    outrows = sorted(rows, key=lambda x: x["discharge"], reverse=True)
    return outrows[0]


def _get_discharge_low_row(rows: list[NormRowDischarge]):
    if len(rows) == 0:
        return None
    outrows = sorted(rows, key=lambda x: x["discharge"])
    return outrows[0]


def _get_temp_high_row(rows: list[NormRowTemperature]):
    if len(rows) == 0:
        return None
    outrows = sorted(rows, key=lambda x: x["temperature"], reverse=True)
    return outrows[0]


def _get_temp_low_row(rows: list[NormRowTemperature]):
    if len(rows) == 0:
        return None
    outrows = sorted(rows, key=lambda x: x["temperature"])
    return outrows[0]


def _get_back_date(curr_dt: datetime.datetime, days: int):
    delta = datetime.timedelta(days=days)
    back_datetime = curr_dt - delta
    back_date = back_datetime.date()
    return back_date


def _get_curr_date():
    return datetime.datetime.now(tz=_get_tz_utc()).replace(microsecond=0)


def _build_stats(
    site: Site,
    url: str,
    rows: list[NormRow],
    curr_dt: datetime.datetime,
    back_date: datetime.date,
):
    if len(rows) == 0:
        return None
    discharge = _build_stats_discharge(rows) if site["feature_discharge"] else None
    temp = _build_stats_temp(rows) if site["feature_temperature"] else None
    ret: Stat = {
        "site_no": site["site_no"],
        "site_name_full": site["name_full"],
        "site_name_short": site["name_short"],
        "site_region": site["region"],
        "site_timezone": site["timezone"],
        "data_url": url,
        "rowcount": len(rows),
        "fetch_datetime": curr_dt,
        "begin_date": back_date,
        "discharge_recent_value": (
            None if discharge is None else discharge["recent_value"]
        ),
        "discharge_recent_datetime": (
            None if discharge is None else discharge["recent_datetime"]
        ),
        "discharge_prediction_value": (
            None if discharge is None else discharge["prediction_value"]
        ),
        "discharge_prediction_direction": (
            None if discharge is None else discharge["prediction_direction"]
        ),
        "discharge_high_value": (
            None if discharge is None else discharge["high_value"]
        ),
        "discharge_low_value": (None if discharge is None else discharge["low_value"]),
        "discharge_high_datetime": (
            None if discharge is None else discharge["high_datetime"]
        ),
        "discharge_low_datetime": (
            None if discharge is None else discharge["low_datetime"]
        ),
        "temp_recent_value": (None if temp is None else temp["recent_value"]),
        "temp_recent_datetime": (None if temp is None else temp["recent_datetime"]),
        "temp_prediction_value": (None if temp is None else temp["prediction_value"]),
        "temp_prediction_direction": (
            None if temp is None else temp["prediction_direction"]
        ),
        "temp_high_value": (None if temp is None else temp["high_value"]),
        "temp_low_value": (None if temp is None else temp["low_value"]),
        "temp_high_datetime": (None if temp is None else temp["high_datetime"]),
        "temp_low_datetime": (None if temp is None else temp["low_datetime"]),
    }
    return ret


def _build_stats_discharge(allrows: list[NormRowDischarge]):
    rows = list(filter(lambda x: x["discharge"] is not None, allrows))
    high_row = _get_discharge_high_row(rows)
    low_row = _get_discharge_low_row(rows)
    if high_row is None or low_row is None:
        return None
    recent = rows[0]
    recent_discharges = _get_recent_discharges(rows)
    prediction = get_prediction_info(recent_discharges, PREDICTION_COUNT)
    ret: StatDischarge = {
        "recent_value": recent["discharge"],
        "recent_datetime": recent["datetime"],
        "prediction_value": prediction["values"][-1],
        "prediction_direction": prediction["direction"],
        "high_value": high_row["discharge"],
        "low_value": low_row["discharge"],
        "high_datetime": high_row["datetime"],
        "low_datetime": low_row["datetime"],
    }
    return ret


def _build_stats_temp(allrows: list[NormRowTemperature]):
    rows = list(filter(lambda x: x["temperature"] is not None, allrows))
    high_row = _get_temp_high_row(rows)
    low_row = _get_temp_low_row(rows)
    if high_row is None or low_row is None:
        return None
    recent = rows[0]
    recent_temps = _get_recent_temps(rows)
    prediction = get_prediction_info(recent_temps, PREDICTION_COUNT)
    ret: StatTemp = {
        "recent_value": recent["temperature"],
        "recent_datetime": recent["datetime"],
        "prediction_value": prediction["values"][-1],
        "prediction_direction": prediction["direction"],
        "high_value": high_row["temperature"],
        "low_value": low_row["temperature"],
        "high_datetime": high_row["datetime"],
        "low_datetime": low_row["datetime"],
    }
    return ret


def _build_for_site(
    site: Site,
    raw: str,
    url: str,
    curr_dt: datetime.datetime,
    begin_date: datetime.date,
):
    clean = _cleanup(raw)
    if clean is None:
        return None
    rawrows = _to_csv(clean)
    normrows = _normalize_doc(site, rawrows)
    stats = _build_stats(site, url, normrows, curr_dt, begin_date)
    return stats


def _process_for_site(site: Site):
    curr_dt = _get_curr_date()
    begin_date = _get_back_date(curr_dt, 1)
    fetchres = _fetch(site, begin_date)
    stats = _build_for_site(
        site, fetchres["text"], fetchres["url"], curr_dt, begin_date
    )
    return stats


def process_all_sites():
    ret: Stats = {}
    for site in SITES:
        stats = _process_for_site(site)
        if stats is None:
            continue
        ret[site["site_no"]] = stats
    return ret


if __name__ == "__main__":
    pprint(process_all_sites())
