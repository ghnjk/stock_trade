#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: date_utils
@author: jkguo
@create: 2022/3/31
"""
import time
import datetime
import pytz


def now_time_str(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(fmt)


def datetime2timestamp(datetime_str: str) -> float:
    return time.mktime(datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").timetuple())


def timeStr2datetime(datetime_str: str):
    return datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")


def timestamp2datetime(ts):
    return datetime.datetime.fromtimestamp(ts)


def timestamp2datetime_str(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def timestamp2date_str(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def timeStr2timestamp(time_str: str, timezone=None):
    if timezone is None:
        timezone = pytz.timezone('local')
    local_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    local_time = timezone.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    timestamp = utc_time.timestamp()
    return timestamp
