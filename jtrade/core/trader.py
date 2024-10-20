#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: trader
@author: jkguo
@create: 2024/10/19
"""
from jtrade.models.dto import TradeOrderDto, TradeOrderStatus, StockStatus
from jtrade.utils import date_utils
from jtrade.core.stock_manager import StockManager
import random


class StockTraderBase(object):

    def open_position(self, order: TradeOrderDto):
        """
        开仓买入股票
        :param order:
        :return:
        """
        raise NotImplementedError

    def close_position(self, order: TradeOrderDto):
        """
        平仓卖出股票
        :param order:
        :return:
        """
        raise NotImplementedError


class KLineMockTrader(StockTraderBase):
    """
   用于测试的模拟交易类
    """

    def __init__(self, stock_manager: StockManager):
        self.buy_orders: dict[str, TradeOrderDto] = {}
        self.sell_orders: dict[str, TradeOrderDto] = {}
        self.stock_manager = stock_manager

    def open_position(self, order: TradeOrderDto):
        """
        开仓买入股票
        :param order:
        :return:
        """
        order.order_id = date_utils.now_time_str("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        self.buy_orders[order.order_id] = order
        return order.order_id

    def close_position(self, order: TradeOrderDto):
        """
        平仓卖出股票
        :param order:
        :return:
        """
        order.order_id = date_utils.now_time_str("%Y%m%d%H%M%S") + str(random.randint(100, 999))
        self.sell_orders[order.order_id] = order
        return order.order_id

    def on_kline_update(self, cur_time: str, cur_price: float):
        """
        用于模拟交易，更新股票价格
        :param cur_time:
        :param cur_price:
        :return:
        """
        stock_has_change = False
        # 检查所有买入订单，如果当前价格小于买入价格，则执行买入操作
        need_del_buy_order_id = []
        for order_id in self.buy_orders.keys():
            order = self.buy_orders[order_id]
            if order.price >= cur_price:
                # order.price = cur_price
                # order.total_amount = order.price * order.quantity
                # order.ext_fee, order.ext_detail = calc_hk_ext_fee(order.total_amount)
                order.order_status = TradeOrderStatus.ALL_TRADED
                order.complete_time = cur_time
                self.stock_manager.on_stock_buy_status_change(order)
                need_del_buy_order_id.append(order.order_id)
                stock_has_change = True
        for order_id in need_del_buy_order_id:
            del self.buy_orders[order_id]
        # 检查所有卖出订单，如果当前价格大于卖出价格，则执行卖出操作
        need_del_sell_order_id = []
        for order_id in self.sell_orders.keys():
            order = self.sell_orders[order_id]
            if order.price <= cur_price:
                # order.price = cur_price
                # order.total_amount = order.price * order.quantity
                # order.ext_fee, order.ext_detail = calc_hk_ext_fee(order.total_amount)
                order.order_status = TradeOrderStatus.ALL_TRADED
                order.complete_time = cur_time
                self.stock_manager.on_stock_sell_status_change(order)
                need_del_sell_order_id.append(order.order_id)
                stock_has_change = True
        for order_id in need_del_sell_order_id:
            del self.sell_orders[order_id]
        # 如果当前时间在16:00:00之后，则取消所有订单
        if cur_time[-8:] >= "16:00:00":
            for order_id in self.buy_orders.keys():
                order = self.buy_orders[order_id]
                order.order_status = TradeOrderStatus.CANCELLED
                self.stock_manager.on_stock_buy_status_change(order)
            self.buy_orders = {}
            for order_id in self.sell_orders.keys():
                order = self.sell_orders[order_id]
                order.order_status = TradeOrderStatus.CANCELLED
                self.stock_manager.on_stock_sell_status_change(order)
            self.sell_orders = {}
        if stock_has_change:
            # 打印所有股票信息
            stocks = self.stock_manager.load_all_valid_stocks()
            print(f"> 持仓信息")
            for stock_id, stock in stocks.items():
                if stock.status == StockStatus.BUYING:
                    continue
                print(f"> {stock.stock_code} {stock.quantity} {stock.buy_price}")
