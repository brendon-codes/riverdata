#!/usr/bin/env python3

from typing import TypedDict
from decimal import Decimal
import datetime


class Park(TypedDict):
    name: str
    region: str
    timezone: str
    site_no_discharge: str
    site_no_temperature: str


class ParkStat(TypedDict):
    park_name: str
    park_region: str
    park_timezone: str
    discharge_recent_value: Decimal | None
    discharge_prediction_value: Decimal | None
    discharge_recent_datetime: datetime.datetime | None
    temp_recent_value: Decimal | None


class Stat(TypedDict):
    site_no: str
    site_name_short: str
    site_name_full: str
    site_region: str
    data_url: str
    rowcount: int
    fetch_datetime: datetime.datetime
    begin_date: datetime.date
    discharge_recent_value: Decimal | None
    discharge_recent_datetime: datetime.datetime | None
    discharge_prediction_value: Decimal | None
    discharge_prediction_direction: int | None
    discharge_high_value: Decimal | None
    discharge_low_value: Decimal | None
    discharge_high_datetime: datetime.datetime | None
    discharge_low_datetime: datetime.datetime | None
    temp_recent_value: Decimal | None
    temp_recent_datetime: datetime.datetime | None
    temp_prediction_value: Decimal | None
    temp_prediction_direction: int | None
    temp_high_value: Decimal | None
    temp_low_value: Decimal | None
    temp_high_datetime: datetime.datetime | None
    temp_low_datetime: datetime.datetime | None


class Site(TypedDict):
    site_no: str
    name_full: str
    name_short: str
    region: str
    timezone: str
    feature_discharge: bool
    feature_temperature: bool


Stats = dict[str, Stat]
ParkStats = list[ParkStat]
