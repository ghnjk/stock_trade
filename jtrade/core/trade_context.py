#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: trade_context
@author: jkguo
@create: 2024/10/18
"""
import typing

from futu import TrdMarket, TrdEnv
from jtrade.models.mysql_backend import MysqlBackend, TradeAccountDto
from jtrade.core.futu_sdk import FutuSdk


class TradeContext(object):

    def __init__(self):
        self.trade_env = TrdEnv.SIMULATE
        self.trade_market = TrdMarket.HK
        self.account_name: str = ""
        self._back_end: typing.Optional[MysqlBackend] = None

    def backend(self) -> MysqlBackend:
        if self._back_end is None:
            raise Exception("TradeContext not initialized. backend is None")
        return self._back_end

    def validate_account(self, acc_dto: TradeAccountDto):
        if self.trade_env != acc_dto.trade_env:
            raise Exception(f"account {acc_dto.account_name} trade_env: {acc_dto.trade_env} not "
                            f"consist with {self.trade_env}")
        if self.trade_market != acc_dto.trade_market:
            raise Exception(f"account {acc_dto.account_name} trade_env: {acc_dto.trade_market} not "
                            f"consist with {self.trade_market}")
        if self.account_name != acc_dto.account_name:
            raise Exception(f"account {acc_dto.account_name} trade_env: {acc_dto.account_name} not "
                            f"consist with {self.account_name}")
        return True

    @staticmethod
    def futu_sdk() -> FutuSdk:
        return FutuSdk()


__TRADE_CONTEXT__ = TradeContext()


def init_context(trade_env: str, trade_market: str, account_name: str, db_config: dict):
    __TRADE_CONTEXT__.trade_env = trade_env
    __TRADE_CONTEXT__.trade_market = trade_market
    __TRADE_CONTEXT__.account_name = account_name
    __TRADE_CONTEXT__._back_end = MysqlBackend(trade_env, trade_market,
                                               host=db_config.get("host", "127.0.0.1"),
                                               port=db_config.get("port", 3306),
                                               user=db_config.get("user", "root"),
                                               password=db_config["password"],
                                               echo_stdout=False
                                               )


def get_context() -> TradeContext:
    return __TRADE_CONTEXT__
