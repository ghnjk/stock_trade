#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: account
@author: jkguo
@create: 2024/10/18
"""
from jtrade.models.dto import TradeAccountDto
from jtrade.core.trade_context import get_context
import logging


class Account(object):

    def __init__(self, account_name: str):
        self.acc_dto: TradeAccountDto = self.__init_account(account_name)
        self.account_name = self.acc_dto.account_name
        self.logger = logging.getLogger("account")

    @staticmethod
    def __init_account(account_name: str):
        ctx = get_context()
        acc = ctx.backend().trade_account_repo().get(account_name)
        if acc is None:
            raise Exception("Account not found: {}".format(account_name))
        return acc

    def check_balance_enough(self, amount: float):
        return self.acc_dto.account_balance >= amount

    def sub_balance(self, amount: float, desc: str):
        """
        账户扣除金额
        :param amount:
        :param desc:
        :return:
        """
        amount = round(amount, 4)
        assert self.acc_dto.account_balance >= amount
        pre_balance = self.acc_dto.account_balance
        self.acc_dto.account_balance -= amount
        self.acc_dto.account_balance = round(self.acc_dto.account_balance, 4)
        self.logger.info(f"Account {self.account_name} pre_balance: {pre_balance} sub {amount} =  balance:"
                         f" {self.acc_dto.account_balance} desc: {desc}")
        ctx = get_context()
        repo = ctx.backend().trade_account_repo()
        repo.save(self.acc_dto)
        return True

    def add_balance(self, amount: float, desc: str):
        """
        账户增加金额
        :param amount:
        :param desc:
        :return:
        """
        amount = round(amount, 4)
        pre_balance = self.acc_dto.account_balance
        self.acc_dto.account_balance += amount
        self.acc_dto.account_balance = round(self.acc_dto.account_balance, 4)
        self.logger.info(f"Account {self.account_name} pre_balance: {pre_balance} + {amount} =  balance:"
                         f" {self.acc_dto.account_balance} desc: {desc}")
        ctx = get_context()
        repo = ctx.backend().trade_account_repo()
        repo.save(self.acc_dto)
        return True

    def get_available_balance(self) -> float:
        return self.acc_dto.account_balance
