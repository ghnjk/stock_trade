#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: test
@author: jkguo
@create: 2024/10/11
"""
from futu import OpenQuoteContext, KLType, RET_OK, TrdMarket, TrdEnv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import matplotlib.dates as mdates
from pandas import DataFrame
import datetime
import numpy as np
from jtrade.core.trade_context import init_context, get_context


def moving_average_convolve(a, n=3):
    window = np.ones(int(n))/float(n)
    return np.convolve(a, window, 'valid')


def moving_sum_convolve(a, n=3):
    window = np.ones(int(n))
    return np.convolve(a, window, 'same')


def test_get_stock_price(stock_code: str):
    from jtrade.core.stock_k_linke_lib import StockKLineLib, StockKLineRepo
    ctx = get_context()
    lib = StockKLineLib(
        stock_code, ctx.backend().stock_k_line_repo(stock_code),
        ctx.futu_sdk()
    )
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=10)
    start = start_date.strftime('%Y-%m-%d')
    end = end_date.strftime('%Y-%m-%d')
    start = "2024-09-01 09:30:00"
    end = "2024-10-18 16:00:00"
    df = lib.query(start, end)
    df.to_csv(stock_code + '.csv')
    plt.figure(figsize=(12, 9))
    plt.subplot(3, 1, 1)
    y = df["close"]
    x = range(len(y))
    plt.plot(x, y, color='b', label='price')
    short_avg_point = 1
    ma_1_y = moving_average_convolve(y, short_avg_point)
    ma_1_y = np.insert(ma_1_y, 0, y[:short_avg_point - 1])
    plt.plot(x, ma_1_y, color='r', label='ma_1')
    long_avg_point = 3
    ma_2_y = moving_average_convolve(y, long_avg_point)
    ma_2_y = np.insert(ma_2_y, 0, y[:long_avg_point - 1])
    plt.plot(x, ma_2_y, color='y', label='ma_2')
    plt.title(f"{stock_code} price")
    plt.legend()
    plt.grid()
    plt.subplot(3, 1, 2)
    ma_diff = ma_1_y - ma_2_y
    plt.fill_between(x, ma_diff, where=(ma_diff > 0), color='red', alpha=0.5, interpolate=True)
    plt.fill_between(x, ma_diff, where=(ma_diff < 0), color='green', alpha=0.5, interpolate=True)
    plt.grid()
    plt.subplot(3, 1, 3)
    ma_diff = moving_sum_convolve(ma_diff, n=120)
    plt.fill_between(x, ma_diff, where=(ma_diff > 0), color='red', alpha=0.5, interpolate=True)
    plt.fill_between(x, ma_diff, where=(ma_diff < 0), color='green', alpha=0.5, interpolate=True)
    plt.grid()
    plt.show()


def init_dev_trade_context():
    init_context(
        "trade_dev_env", TrdMarket.HK,
        "test_account",  db_config={
            "user": "jk_dev",
            "password": "jk_dev"
        }
    )


if __name__ == '__main__':
    import matplotlib
    from jtrade.utils import log_util
    log_util.set_stdout_logger(logger="mysql.backend")
    log_util.set_stdout_logger(logger="futu_sdk")
    matplotlib.use('TkAgg')
    init_dev_trade_context()
    test_get_stock_price("HK.00700")
