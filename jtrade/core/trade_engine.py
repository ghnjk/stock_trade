#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: trade_engine
@author: jkguo
@create: 2024/10/18
"""
import random
import time
import typing

import pytz
import datetime
from jtrade.core.stock_manager import StockManager
from jtrade.core.stock_k_linke_lib import StockKLineLib
from jtrade.utils import date_utils
from jtrade.core.trade_alg_base import TradeAlgBase, TradeDecision
from jtrade.core.trader import StockTraderBase
from jtrade.core.account import Account
from jtrade.models.dto import TradeOrderStatus, TradeOrderDto
from jtrade.core.trade_context import get_context
from jtrade.utils.fee_util import calc_hk_ext_fee
from futu import TrdSide


class TradeEngine(object):
    """
    交易引擎
    """

    def __init__(self, stock_manager: StockManager, kline_lib: StockKLineLib,
                 trade_alg: TradeAlgBase, trader: StockTraderBase):
        self.stock_code = stock_manager.stock_code
        self.account: Account = stock_manager.account
        self.stock_manager: StockManager = stock_manager
        self.kline_lib: StockKLineLib = kline_lib
        self.trade_alg: TradeAlgBase = trade_alg
        self.trader: StockTraderBase = trader
        self.timezone = pytz.timezone('Asia/Shanghai')

    def on_rt_data(self, cur_data: dict):
        """
        处理 实时分时回调
        :param cur_data: 实时分时回调数据
        字段	类型	说明
            code	str	股票代码
            name	str	股票名称
            time	str	时间 格式：yyyy-MM-dd HH:mm:ss 港股和 A 股市场默认是北京时间，美股市场默认是美东时间
            is_blank	bool	数据状态 False：正常数据 True：伪造数据
            opened_mins	int	零点到当前多少分钟
            cur_price	float	当前价格
            last_close	float	昨天收盘的价格
            avg_price	float	平均价格 对于期权，该字段为 None
            volume	float	成交量
            turnover	float	成交金额
        :return:
        """
        assert cur_data["code"] == self.stock_code
        # 准备算法参数
        alg_params = self._prepare_alg_params(cur_data)
        # 生成交易决策
        decisions = self.trade_alg.gen_decision(alg_params)
        self._print_decisions(decisions, alg_params)
        # 执行交易决策
        for decision in decisions:
            self._execute_decision(decision)

    def _prepare_alg_params(self, cur_data: dict):
        cur_timestamp = date_utils.timeStr2timestamp(
            cur_data["time"],
            self.timezone
        )
        kline_end_timestamp = cur_timestamp - 60
        kline_end_timestamp = kline_end_timestamp / 60 * 60.0
        kline_start_timestamp = kline_end_timestamp - 24 * 3600 * 360
        kline_df = self.kline_lib.query(kline_start_timestamp, kline_end_timestamp)
        x = kline_df["time_key"].values
        y = kline_df["close"].values
        available_balance = self.account.get_available_balance()
        return {
            "stock_code": cur_data["code"],
            "cur_timestamp": cur_timestamp,
            "cur_time_str": cur_data["time"],
            "cur_price": cur_data["cur_price"],
            "available_balance": available_balance,
            "kline_df": kline_df,
            "x": x,
            "y": y,
            "stocks": self.stock_manager.load_all_valid_stocks(),
            "cur_data": cur_data
        }

    def _execute_decision(self, decision: TradeDecision):
        """
        执行交易决策
        :param decision:
        :return:
        """
        if decision is None:
            return
        assert decision.is_valid()
        ctx = get_context()
        if decision.trade_op == TradeDecision.TRADE_OP_BUY:
            # 买入股票
            buy_order = self._build_buy_order(decision)
            self.trader.open_position(buy_order)
            # 新增买入中的股票信息
            self.stock_manager.on_stock_submit_buying(buy_order)
            # 保存订单
            ctx.backend().trade_order_repo(self.account.account_name).store(buy_order)
        else:
            # 卖出股票
            sell_order = self._build_sell_order(decision)
            self.trader.close_position(sell_order)
            # 更新卖出的股票状态
            self.stock_manager.on_stock_submit_selling(sell_order)
            # 保存订单
            ctx.backend().trade_order_repo(self.account.account_name).store(sell_order)

    def _build_buy_order(self, decision: TradeDecision) -> TradeOrderDto:
        """
        生成买入订单
        :param decision:
        :return:
        """
        assert decision.trade_op == TradeDecision.TRADE_OP_BUY
        ctx = get_context()
        order = TradeOrderDto()
        order.trade_env = ctx.trade_env
        order.trade_market = ctx.trade_market
        order.account_name = self.stock_manager.account.acc_dto.account_name
        # order id 需要等回调后才能确定
        order.order_id = ""
        order.trade_side = TrdSide.BUY
        order.order_status = TradeOrderStatus.INITIALIZED
        order.stock_code = decision.stock_code
        # 买入的股票持有id需要自动生成
        order.stock_holding_id = decision.stock_holding_id
        order.quantity = decision.quantity
        order.price = decision.price
        order.total_amount = order.quantity * order.price
        order.ext_fee, order.ext_detail = calc_hk_ext_fee(order.total_amount)
        order.submit_time = datetime.datetime.now()
        order.valid_time = date_utils.timeStr2datetime(
            date_utils.now_time_str("%Y-%m-%d 16:00:00")
        )
        order.trader = decision.trader_name
        order.notes = decision.notes
        order.ext_detail = decision.ext_detail
        return order

    def _build_sell_order(self, decision: TradeDecision) -> TradeOrderDto:
        """
        生成卖出订单
        :param decision:
        :return:
        """
        assert decision.trade_op == TradeDecision.TRADE_OP_SELL
        ctx = get_context()
        order = TradeOrderDto()
        order.trade_env = ctx.trade_env
        order.trade_market = ctx.trade_market
        order.account_name = self.stock_manager.account.acc_dto.account_name
        # order id 需要等回调后才能确定
        order.order_id = ""
        order.trade_side = TrdSide.SELL
        order.order_status = TradeOrderStatus.INITIALIZED
        order.stock_code = decision.stock_code
        order.stock_holding_id = decision.stock_holding_id
        order.quantity = decision.quantity
        order.price = decision.price
        order.total_amount = order.quantity * order.price
        order.ext_fee, order.ext_detail = calc_hk_ext_fee(order.total_amount)
        order.submit_time = datetime.datetime.now()
        order.valid_time = date_utils.timeStr2datetime(
            date_utils.now_time_str("%Y-%m-%d 16:00:00")
        )
        order.trader = decision.trader_name
        order.notes = decision.notes
        order.ext_detail = decision.ext_detail
        return order

    def _print_decisions(self, decisions: typing.List[TradeDecision], alg_params: dict):
        if len(decisions) == 0:
            return
        cur_time_str = alg_params["cur_time_str"]
        stock_code = alg_params["stock_code"]
        cur_price = alg_params["cur_price"]
        print(f"** 周期: {cur_time_str} 股票代码: {stock_code} 价格: {cur_price} **")
        for decision in decisions:
            print(str(decision))


if __name__ == '__main__':
    print(
        calc_hk_ext_fee(141900)
    )
