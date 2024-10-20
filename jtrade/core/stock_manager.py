#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: stock_manager
@author: jkguo
@create: 2024/10/18
"""
import typing
import logging
from jtrade.core.account import Account
from jtrade.models.dto import StockDto, TradeOrderDto, StockStatus, TradeOrderStatus
from jtrade.core.trade_context import get_context
from futu import TrdSide


class StockManager(object):
    """
    股票管理器
    """

    def __init__(self, account: Account, stock_code: str):
        """
        :param account:
        :param stock_code:
        """
        self.account = account
        self.stock_code = stock_code
        self.logger = logging.getLogger("stock_manager")

    def load_all_valid_stocks(self) -> typing.Dict[str, StockDto]:
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_status_list = [
            StockStatus.SELLING, StockStatus.BUYING, StockStatus.HOLDING
        ]
        res = {}
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        for item in stock_repo.query_all(self.stock_code, stock_status_list):
            res[item.stock_holding_id] = item
        return res

    def load_all_sold_stocks(self) -> typing.Dict[str, StockDto]:
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_status_list = [
            StockStatus.SOLD
        ]
        res = {}
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        for item in stock_repo.query_all(self.stock_code, stock_status_list):
            res[item.stock_holding_id] = item
        return res

    def on_stock_submit_selling(self, order: TradeOrderDto):
        """
        当股票提交卖出时，需要更新持有股票状态
        :param order:
        :return:
        """
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        stock = stock_repo.query_by_holding_id(order.stock_code, order.stock_holding_id)
        if stock is None:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} not found")
        if stock.status != StockStatus.HOLDING:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} status is not HOLDING")
        if stock.quantity != order.quantity:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} quantity is not {order.quantity}")
        stock.status = StockStatus.SELLING
        stock.sell_price = order.price
        stock.sell_total_amount = order.total_amount
        stock.sell_all_ext_fee = order.ext_fee
        stock.sell_order_id = order.order_id
        stock_repo.save(stock)

    def on_stock_sell_status_change(self, order: TradeOrderDto):
        """
        当股票卖出时，需要更新持有股票状态
        :param order:
        :return:
        """
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        stock = stock_repo.query_by_holding_id(order.stock_code, order.stock_holding_id)
        if stock is None:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} not found")
        if stock.status != StockStatus.SELLING:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} status is not SELLING")
        if order.order_status == TradeOrderStatus.ALL_TRADED:
            # 全部卖出
            stock.status = StockStatus.SOLD
            stock.sell_price = order.price
            stock.sell_total_amount = order.total_amount
            stock.sell_all_ext_fee = order.ext_fee
            stock.sell_time = order.complete_time
            # 计算收益
            stock.trade_profit = stock.sell_total_amount - stock.buy_total_amount - stock.sell_all_ext_fee - stock.buy_all_ext_fee
            # 交易费用结算
            self.account.add_balance(order.total_amount, f"卖出股票 {order.stock_code} {order.stock_holding_id}")
            self.account.sub_balance(order.ext_fee, f"交易费用 {order.stock_code} {order.order_id}")
            stock_repo.save(stock)
        elif order.order_status == TradeOrderStatus.CANCELLED:
            # 取消卖出
            stock.status = StockStatus.HOLDING
            stock.sell_price = 0
            stock.sell_total_amount = 0
            stock.sell_all_ext_fee = 0
            stock_repo.save(stock)
        else:
            # 其他状态
            self.logger.info(f"stock {self.stock_code} {order.stock_holding_id} {order.order_status} ignored.")

    def on_stock_submit_buying(self, order: TradeOrderDto):
        """
        当股票提交买入时，需要更新持有股票状态
        :param order:
        :return:
        """
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        # 扣除余额
        if not self.account.check_balance_enough(order.total_amount + order.ext_fee):
            raise Exception("账户余额不足")
        if not self.account.sub_balance(order.total_amount, f"购买股票 {order.stock_code} {order.stock_holding_id}"):
            raise Exception(f"账户余额不足")
        if not self.account.sub_balance(order.ext_fee, f"交易费用 {order.stock_code} {order.order_id}"):
            raise Exception(f"账户余额不足")
        stock = self._build_stock_from_order(order)
        stock.status = StockStatus.BUYING
        stock_repo.save(stock)

    def on_stock_buy_status_change(self, order: TradeOrderDto):
        """
        当股票买入时，需要更新持有股票状态
        :param order:
        :return:
        """
        ctx = get_context()
        ctx.validate_account(self.account.acc_dto)
        stock_repo = ctx.backend().stock_repo(self.account.account_name)
        stock = stock_repo.query_by_holding_id(order.stock_code, order.stock_holding_id)
        if stock is None:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} not found")
        if stock.status != StockStatus.BUYING:
            raise Exception(f"stock {self.stock_code} {order.stock_holding_id} status is not BUYING")
        if order.order_status == TradeOrderStatus.ALL_TRADED:
            # 全部买入
            stock.status = StockStatus.HOLDING
            stock.buy_price = order.price
            stock.buy_total_amount = order.total_amount
            stock.buy_all_ext_fee = order.ext_fee
            stock.buy_time = order.complete_time
            stock_repo.save(stock)
        elif order.order_status == TradeOrderStatus.CANCELLED:
            # 取消买入
            stock.status = StockStatus.DELETED
            stock_repo.save(stock)
            # 将资金退回
            self.account.add_balance(order.total_amount, f"【退款】买入股票 {order.stock_code} {order.stock_holding_id}")
            self.account.add_balance(order.ext_fee, f"【退款】交易费用 {order.stock_code} {order.order_id}")
        else:
            # 其他状态
            self.logger.info(f"stock {self.stock_code} {order.stock_holding_id} {order.order_status} ignored.")

    @staticmethod
    def _build_stock_from_order(order: TradeOrderDto) -> StockDto:
        assert order.trade_side == TrdSide.BUY
        stock = StockDto()
        stock.trade_env = order.trade_env
        stock.trade_market = order.trade_market
        stock.account_name = order.account_name
        stock.stock_code = order.stock_code
        stock.stock_holding_id = order.stock_holding_id
        stock.status = StockStatus.INIT
        stock.quantity = order.quantity
        stock.buy_price = order.price
        stock.buy_total_amount = order.total_amount
        stock.buy_all_ext_fee = order.ext_fee
        stock.buy_order_id = order.order_id
        return stock
