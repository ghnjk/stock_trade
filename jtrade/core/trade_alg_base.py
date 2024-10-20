#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: trade_alg_base
@author: jkguo
@create: 2024/10/19
"""
import typing


class TradeDecision(object):
    """
    交易决策结果
    """

    TRADE_OP_BUY = "BUY"
    TRADE_OP_SELL = "SELL"

    def __init__(self):
        # 交易类型
        self.trade_op: typing.Optional[str] = None
        # 交易股票
        self.stock_code: typing.Optional[str] = None
        # 交易价格
        self.price: typing.Optional[float] = None
        # 交易数量
        self.quantity: typing.Optional[int] = None
        # 股票持有id
        self.stock_holding_id: typing.Optional[str] = None
        # 交易者名字
        self.trader_name: typing.Optional[str] = None
        # 交易备注（会提交到外部）
        self.notes: typing.Optional[str] = ""
        # 交易其他信息（只内部记录）
        self.ext_detail: typing.Optional[dict] = {}

    def __str__(self):
        return f"{self.trader_name}: {self.trade_op} {self.stock_code} {self.quantity} * {self.price} " \
               f"id: {self.stock_holding_id} note: {self.notes}"

    def is_valid(self):
        if self.trade_op not in [
            TradeDecision.TRADE_OP_BUY,
            TradeDecision.TRADE_OP_SELL
        ]:
            return False
        if self.stock_code is None or len(self.stock_code) == 0:
            return False
        if self.price is None or self.price <= 0:
            return False
        if self.quantity is None or self.quantity <= 0:
            return False
        if self.trade_op == TradeDecision.TRADE_OP_SELL and self.stock_holding_id is None:
            return False
        return True


class TradeAlgBase(object):
    """
    交易算法基类
    """

    def gen_decision(self, alg_params: dict) -> list[TradeDecision]:
        """
        生成交易决策
        :param alg_params: {
            "cur_timestamp": cur_timestamp,
            "cur_time_str": cur_data["time"],
            "cur_price": cur_data["cur_price"],
            "kline_df": kline_df,
            "x": x,
            "y": y,
            "stocks": self.stock_manager.load_all_valid_stocks(),
            "cur_data": cur_data
        }
        :return: list[TradeDecision
        """
        return []
