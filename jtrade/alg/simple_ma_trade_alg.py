#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: simple_ma_trade_alg
@author: jkguo
@create: 2024/10/19
"""
import numpy as np
import pandas as pd
import math
import typing
import time
import random
from jtrade.utils import date_utils
from jtrade.core.trade_alg_base import TradeAlgBase, TradeDecision
from jtrade.models.dto import StockDto, StockStatus
from jtrade.utils.fee_util import calc_expect_sell_price


def period_to_time(p: float) -> str:
    day_count = 60 * 5.5
    days = int(p / day_count)
    # 对hour 四舍五入
    hour = round((p - day_count * days) / 60)
    if days > 0:
        return f"{days}天{hour}小时"
    else:
        return f"{hour}小时"


def calc_moving_sum_convolve(a, n=3):
    window = np.ones(int(n))
    return np.convolve(a, window, 'valid')


def calc_moving_average_convolve(a, n=3):
    window = np.ones(int(n))/float(n)
    return np.convolve(a, window, 'valid')


class SimpleMaTradeAlg(TradeAlgBase):
    """
   简单的均线交易策略
    """

    def __init__(self):
        self.his_sell_prices = []

    def gen_decision(self, alg_params: dict) -> list[TradeDecision]:
        """
        生成交易决策
        :param alg_params: {
            "stock_code": str,
            "cur_timestamp": float,
            "cur_time_str": str, yyyy-mm-dd HH:MM:SS,
            "cur_price": float,
            "available_balance": float,
            "kline_df": pd.DataFrame,
            "x": p.ndarray
            "y": p.ndarray
            "stocks":  typing.Dict[str, StockDto],
            "cur_data": cur_data
        }
        :return: 交易决策列表
        """
        stock_code = alg_params["stock_code"]
        cur_price = alg_params["cur_price"]
        cur_time_str = alg_params["cur_time_str"]
        decisions = []
        stocks: typing.Dict[str, StockDto] = alg_params["stocks"]
        # 查看当前所有持有的股票，计算是否可以卖出
        for holding_id, stock in stocks.items():
            if stock.status != StockStatus.HOLDING:
                continue
            expect_sell_price = calc_expect_sell_price(stock.buy_price, stock.quantity)
            if cur_price >= expect_sell_price:
                sell_price = cur_price
                decisions.append(self.build_sell_decision(stock, sell_price))
                self.his_sell_prices.append((sell_price, alg_params["cur_timestamp"]))
        # 判断当前股价和趋势，决定是否买入
        need_buy, buy_price, buy_quantity = self._calc_buy_price(alg_params)
        if need_buy and buy_price > 0:
            decisions.append(self.build_buy_decision(stock_code, cur_time_str, buy_price, buy_quantity))
        return decisions

    @staticmethod
    def _gen_stock_holding_id(cur_time_str: str) -> str:
        now = cur_time_str.replace("-", "").replace(":", "").replace(" ", "_")
        time_mod = int(time.time() * 10000) % 10000
        rand_int = random.randint(1, 10000)
        return f"{now}.{time_mod}.{rand_int}"

    def build_buy_decision(self, stock_code: str, cur_time_str: str, buy_price, quantity):
        """
        生成买入决策
        :param stock_code:
        ;param cur_time_str:
        :param buy_price:
        :param quantity:
        :return:
        """
        decision = TradeDecision()
        decision.trade_op = TradeDecision.TRADE_OP_BUY
        decision.stock_code = stock_code
        decision.price = buy_price
        decision.quantity = quantity
        decision.stock_holding_id = self._gen_stock_holding_id(cur_time_str) + "_" + str(buy_price)
        decision.trader_name = "simple_ma_trade_alg"
        decision.notes = f"buy-{decision.stock_holding_id}:{buy_price}"
        return decision

    def build_sell_decision(self, stock: StockDto, sell_price: float) -> TradeDecision:
        """
        生成卖出决策
        :param stock:
        :param sell_price:
        :return:
        """
        decision = TradeDecision()
        decision.trade_op = TradeDecision.TRADE_OP_SELL
        decision.stock_code = stock.stock_code
        decision.price = sell_price
        decision.quantity = stock.quantity
        decision.stock_holding_id = stock.stock_holding_id
        decision.trader_name = "simple_ma_trade_alg"
        decision.notes = f"sell-{stock.stock_holding_id}:{sell_price}"
        return decision

    def _gen_hist_sell_wait_time_df(self, y: np.ndarray, cur_price_period) -> pd.DataFrame:
        data = []
        period_begin, period_end = cur_price_period
        n = len(y)
        sell_days = [-1] * n
        stack = []
        for i in range(n):
            price = y[i]
            cur_pos_list = [i]
            while len(stack) > 0:
                pre_p, pos_list = stack[-1]
                expect_sell_price = pre_p * 1.005
                if price >= expect_sell_price:
                    for p in pos_list:
                        sell_days[p] = i - p
                    stack.pop()
                elif price < pre_p:
                    break
                else:
                    stack.pop()
                    cur_pos_list.extend(pos_list)
            stack.append((price, cur_pos_list))
        for i in range(n):
            price = y[i]
            if price < period_begin or price >= period_end:
                continue
            if sell_days[i] > 0:
                data.append(
                    [price, sell_days[i]]
                )
        return pd.DataFrame(data, columns=["price", "sell_wait_time"])

    def _calc_price_period(self, cur_price) -> typing.Tuple[float, float]:
        """
        根据当前价格，计算股票价格的档位区间
        :param cur_price:
        :return:
        """
        period_size = round(cur_price * 0.05, 2)
        period_begin = cur_price - period_size * 0.5
        period_end = period_begin + period_size
        return period_begin, period_end

    def _calc_buy_price(self, alg_params) -> typing.Tuple[bool, float, float]:
        """
        计算买入价格
        :param alg_params:
        :return:
        """
        y: np.ndarray = alg_params["y"]
        cur_time_str = alg_params["cur_time_str"]
        cur_price = alg_params["cur_price"]
        available_balance = alg_params["available_balance"]
        stocks: typing.Dict[str, StockDto] = alg_params["stocks"]
        buy_quantity = 100
        while buy_quantity * cur_price < 20000:
            buy_quantity += 100
        if self._check_above_history_sell(cur_price, alg_params["cur_timestamp"]):
            return False, -1, 0
        # 检测资金
        if available_balance < buy_quantity * cur_price:
            # 资金不够
            # print(f"not enough balance: {available_balance} < {buy_quantity * cur_price}")
            return False, -1, 0
        # 检测是否有相同档位的股票
        cur_price_period = self._calc_price_period(cur_price)
        for holding_id, stock in stocks.items():
            if cur_price_period[0] <= stock.buy_price <= cur_price_period[1]:
                # 有相同档位的股票
                # print(f"have same price stock: {holding_id}")
                return False, -1, 0
        # 判定当前趋势
        last_trand, last_period, his_periods = self._calc_trend(y)
        if last_trand == 'down' and last_period <= np.percentile(his_periods, 80) * 0.66:
            # 下行趋势，且在趋势的前2/3 不买入
            # print(f"{cur_time_str}: 股价 {cur_price} - 下行趋势前2/3 不买入")
            return False, -1, 0
        if last_trand == 'up' and last_period >= np.percentile(his_periods, 80) * 0.33:
            # 上行趋势，且在趋势的后2/3 不买入
            # print(f"{cur_time_str}: 股价 {cur_price} - 上行趋势后2/3 不买入")
            return False, -1, 0
        # 计算历史相似阶段的迈出预期时间
        his_sell_wait_time_df = self._gen_hist_sell_wait_time_df(
            y, cur_price_period
        )
        if len(his_sell_wait_time_df) <= 10:
            # print("not enough history data")
            return False, -1, 0
        wait_p90 = np.percentile(his_sell_wait_time_df["sell_wait_time"], 90)
        wait_avg = np.mean(his_sell_wait_time_df["sell_wait_time"])
        day_period_count = 60 * 5.5
        if wait_avg > day_period_count * 10 or wait_p90 > day_period_count * 20:
            # print(f"{cur_time_str}: 股价 {cur_price} - 预测可卖出时间太长。 历史平均: {period_to_time(wait_avg)} P90： {period_to_time(wait_p90)}")
            return False, -1, 0
        # 买入
        return True, cur_price, buy_quantity

    def _calc_trend(self, y):
        down_periods, up_periods = [], []
        short_avg_point = 3
        long_avg_point = 10
        ma_1_y = calc_moving_average_convolve(y, short_avg_point)
        ma_2_y = calc_moving_average_convolve(y, long_avg_point)
        ma_diff = ma_1_y[long_avg_point - short_avg_point:] - ma_2_y
        ma_diff: np.ndarray = calc_moving_sum_convolve(ma_diff, n=60)
        cur_period_begin_idx = -1
        cur_period_begin_v = 0
        for i in range(len(ma_diff)):
            v = ma_diff[i]
            if cur_period_begin_idx < 0:
                if v != 0:
                    cur_period_begin_idx = i
                    cur_period_begin_v = v
            elif v * cur_period_begin_v <= 0:
                if cur_period_begin_v > 0:
                    up_periods.append(i - cur_period_begin_idx)
                else:
                    down_periods.append(i - cur_period_begin_idx)
                if v != 0:
                    cur_period_begin_idx = i
                    cur_period_begin_v = v
        if ma_diff[-1] > 0:
            last_trand = "up"
            return last_trand, len(ma_diff) - cur_period_begin_idx, up_periods
        else:
            last_trand = "down"
            return last_trand, len(ma_diff) - cur_period_begin_idx, down_periods

    def _check_above_history_sell(self, cur_price, cur_timestamp):
        is_above = False
        pop_idx = []
        for idx in range(len(self.his_sell_prices)):
            (sell_price, sell_timestamp) = self.his_sell_prices[idx]
            if cur_timestamp - sell_timestamp > 60 * 60 * 24 * 10:
                pop_idx.append(idx)
            elif sell_price <= cur_price:
                is_above = True
        if len(pop_idx) > 0:
            pop_idx.sort(reverse=True)
            for idx in pop_idx:
                self.his_sell_prices.pop(idx)
        return is_above
