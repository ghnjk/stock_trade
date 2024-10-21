#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: kline_mock_trade_runner
@author: jkguo
@create: 2024/10/19
"""
import sys

import pandas as pd

sys.path.append("..")
from futu import TrdMarket, TrdEnv
import matplotlib.pyplot as plt
from jtrade.core.trade_context import init_context, get_context
from jtrade.utils import date_utils
from jtrade.core.trade_engine import Account, StockManager, StockKLineLib, TradeEngine
from jtrade.models.dto import TradeAccountDto, StockStatus
from jtrade.alg.simple_ma_trade_alg import SimpleMaTradeAlg


STOCK_CODE = "HK.00700"
# STOCK_CODE = "HK.02628"
ACCOUNT_INIT_BALANCE = 200000

MOCK_START_DATE = "2024-10-10"
MOCK_END_DATE = "2024-10-21"


def prepare_mock_context():
    account_name = "mock_acc_" + date_utils.now_time_str("%Y%m%d_%H%M%S")
    init_context(
        "kline_mock_env", TrdMarket.HK,
        account_name, db_config={
            "user": "jk_dev",
            "password": "jk_dev"
        }
    )


def prepare_account() -> Account:
    ctx = get_context()
    dto = ctx.backend().trade_account_repo().get(ctx.account_name)
    if dto is not None:
        return dto
    dto = TradeAccountDto()
    dto.trade_env = ctx.trade_env
    dto.trade_market = ctx.trade_market
    dto.account_name = ctx.account_name
    dto.trade_pwd = ""
    dto.account_balance = ACCOUNT_INIT_BALANCE
    ctx.backend().trade_account_repo().save(dto)
    account = Account(dto.account_name)
    return account


def prepare_stock_manager(account):
    stock_manager = StockManager(
        account=account, stock_code=STOCK_CODE
    )
    return stock_manager


def prepare_kline_lib(stock_manager):
    ctx = get_context()
    lib = StockKLineLib(
        stock_manager.stock_code,
        ctx.backend().stock_k_line_repo(stock_manager.stock_code),
        ctx.futu_sdk()
        # , force_sync_from_futu=True
    )
    return lib


def prepare_trader(stock_manager):
    from jtrade.core.trader import KLineMockTrader
    trader = KLineMockTrader(stock_manager)
    return trader


def output_mock_report(start_mock_date: str, end_mock_date: str, last_price: float, account: Account, stock_manager: StockManager):
    print("# 股票模拟交易报告")
    print("----------------")
    print(f" - 账户： {account.account_name}")
    print(f" - 股票代码： {stock_manager.stock_code}")
    print(" - 开始日期：{0}".format(start_mock_date))
    print(" - 结束日期：{0}".format(end_mock_date))
    print(" - 账户余额：{0}".format(round(account.acc_dto.account_balance, 2)))
    print("## 当前持仓情况:")
    stocks = stock_manager.load_all_valid_stocks()
    all_quantity = 0
    all_cost = 0
    for stock_id, stock in stocks.items():
        if stock.status == StockStatus.BUYING:
            continue
        print(f" - {stock.stock_code} {stock.quantity} * {stock.buy_price} = {stock.quantity * stock.buy_price}"
              f" id: {stock.stock_holding_id}")
        all_quantity += stock.quantity
        all_cost += stock.quantity * stock.buy_price
    if all_quantity > 0:
        print(f"** 当前总数量：{all_quantity}")
        print(f"** 当前总成本：{all_cost}")
        print(f"** 当前平均成本：{round(all_cost / all_quantity, 2)}")
        print(f"** 当前股价：{last_price}")
        print(f"** 持仓估值：{last_price * all_quantity}")
    print(f"** 当前账面总资产：{round(account.acc_dto.account_balance + last_price * all_quantity, 2)}")
    print("## 历史交易记录：")
    stocks = stock_manager.load_all_sold_stocks()
    total_profit = 0
    for stock_id, stock in stocks.items():
        print(f" - {stock.stock_code} {stock.quantity}"
              f" {stock.buy_time} 买入价 {stock.buy_price} "
              f" {stock.sell_time} 卖出价 {stock.sell_price}"
              f" 收益 {stock.trade_profit} 买卖手续费 {round(stock.sell_all_ext_fee + stock.buy_all_ext_fee, 2)}"
              f" id: {stock.stock_holding_id}")
        total_profit += stock.trade_profit
    print("----------------")
    print(f"** 总交易次数：{len(stocks)}")
    print(f"** 总交易收益：{round(total_profit, 2)}")


def plot_account_trade(start_mock_date: str, end_mock_date: str, stock_manager: StockManager, kline_lib: StockKLineLib):
    df = kline_lib.query(start_mock_date, end_mock_date)
    x = df["time_key"].to_list()
    y = df["close"]
    # 创建图像和坐标轴
    fig, ax = plt.subplots()
    # 绘制股价曲线
    ax.plot(range(len(x)), y, color='gray', label='price')
    # 设置x轴标签格式
    import matplotlib.dates as mpl_dates
    # date_format = mpl_dates.DateFormatter('%Y-%m-%d')  # 设置日期格式
    # ax.xaxis.set_major_formatter(date_format)  # 设置主要刻度的日期格式
    # 旋转日期标签
    # plt.xticks(rotation=45)
    # # 添加主要日期刻度和次要日期刻度
    # ax.xaxis.set_major_locator(mpl_dates.WeekdayLocator())  # 设置主要刻度为每月
    # ax.xaxis.set_minor_locator(mpl_dates.DayLocator())  # 设置次要刻度为每周
    # 调整图像大小
    fig.set_size_inches(10, 6)  # 设置图像大小为10x6英寸
    stocks = stock_manager.load_all_sold_stocks()
    y_max = max(y)
    for stock_id, stock in stocks.items():
        # buy time
        x_value = x.index(stock.buy_time)
        ax.axvline(x_value, color='blue', linestyle='-', linewidth=0.5, label='buy')
        label = stock.buy_time[5:10]
        ax.annotate(label, xy=(x_value, y_max), xytext=(x_value + 0.5, y_max - 1),
                    arrowprops=dict(arrowstyle='->'))
        # sell time
        x_value = x.index(stock.sell_time)
        ax.axvline(x.index(stock.sell_time), color='r', linestyle='-.', linewidth=0.5, label='sell')
        label = stock.sell_time[5:10]
        ax.annotate(label, xy=(x_value, y_max), xytext=(x_value + 0.5, y_max - 1),
                    arrowprops=dict(arrowstyle='->'))
    stocks = stock_manager.load_all_valid_stocks()
    for stock_id, stock in stocks.items():
        if stock.status == StockStatus.BUYING:
            continue
        x_value = x.index(stock.buy_time)
        ax.axvline(x_value, color='yellow', linestyle='-', linewidth=0.5, label='buy')
        label = stock.buy_time[5:10]
        ax.annotate(label, xy=(x_value, y_max), xytext=(x_value + 0.5, y_max - 1),
                    arrowprops=dict(arrowstyle='wedge'))
    # 显示图像
    plt.show()


def mock_trade():
    print("初始化...")
    prepare_mock_context()
    account = prepare_account()
    stock_manager = prepare_stock_manager(account)
    kline_lib = prepare_kline_lib(stock_manager)
    trader = prepare_trader(stock_manager)
    trade_engine = TradeEngine(stock_manager, kline_lib, SimpleMaTradeAlg(), trader)
    print("加载历史K线数据...")
    df = kline_lib.query("2018-01-01", MOCK_END_DATE)
    print("开始模拟交易...")
    start_mock_date = None
    end_mock_date = None
    last_price = 0
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if row_dict["time_key"] < MOCK_START_DATE:
            continue
        if row_dict["time_key"].endswith("09:30:00"):
            trade_date = row_dict["time_key"][:10]
            print("交易日：{0}".format(trade_date))
            if start_mock_date is None:
                start_mock_date = trade_date
            end_mock_date = trade_date
        cur_data = {
            "code": row_dict["code"],
            "time": row_dict["time_key"],
            "cur_price": row_dict["close"]
        }
        last_price = row_dict["close"]
        trade_engine.on_rt_data(cur_data)
        trader.on_kline_update(row_dict["time_key"], last_price)
    output_mock_report(start_mock_date, end_mock_date, last_price, account, stock_manager)
    plot_account_trade(start_mock_date, end_mock_date, stock_manager, kline_lib)


def init_sys():
    import matplotlib
    from jtrade.utils import log_util
    # log_util.set_stdout_logger(logger="mysql.backend")
    log_util.set_stdout_logger(logger="futu_sdk")
    # log_util.set_stdout_logger(logger="account")
    log_util.set_stdout_logger(logger="stock_manager")
    matplotlib.use('TkAgg')


if __name__ == '__main__':
    init_sys()
    mock_trade()
