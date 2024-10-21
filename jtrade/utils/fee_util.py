#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: fee_util
@author: jkguo
@create: 2024/10/19
"""
import typing
import math


def calc_expect_sell_price(buy_price: float, quantity: int) -> float:
    """
    计算预期卖出价格
    :param buy_price:
    :param quantity:
    :return:
    """
    total_buy_amount = buy_price * quantity
    buy_fee, _ = calc_hk_ext_fee(total_buy_amount)
    return round((total_buy_amount + buy_fee * 2 * 2) / quantity, 2) + 0.01
    # for rate in [1.006, 1.007, 1.008, 1.009, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09,
    #              1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 3, 4, 5]:
    #     expect_sell_price = buy_price * rate
    #     total_sell_amount = expect_sell_price * quantity
    #     sell_fee, _ = calc_hk_ext_fee(total_sell_amount)
    #     profit = total_sell_amount - total_buy_amount - buy_fee - sell_fee
    #     if profit > buy_fee + sell_fee and profit >= 0:
    #         return expect_sell_price
    # raise Exception("计算预期卖出价格失败")


def calc_hk_ext_fee(total_amount: float) -> typing.Tuple[float, dict]:
    """
    佣金: 0.03%  42.57 每笔订单最低3.00港元（免佣期内不收取）
    平台交易费： 按套餐1 15
    交收费： 0.002%  2.84 （每次成交最低2.00港元，最高100.00港元）
    印花税： 0.1%  142
    交易费： 0.00565% 8.02
    证券会征费： 0.0027% 3.83
    财汇局征费： 0.00015% 0.21
    :param total_amount:
    :return: ext_fee, ext_detail
    """
    ext_fee = 0
    ext_detail = {}
    # 佣金
    commission = math.ceil(total_amount * 100 * 0.0003) / 100.0
    if commission < 3:
        commission = 3
    ext_fee += commission
    ext_detail["佣金"] = commission
    # 平台交易费
    platform_fee = 15
    ext_fee += platform_fee
    ext_detail["平台交易费"] = platform_fee
    # 交收费
    stamp_duty = math.ceil(total_amount * 100 * 0.00002) / 100
    if stamp_duty < 2:
        stamp_duty = 2
    ext_fee += stamp_duty
    ext_detail["交收费"] = stamp_duty
    # 印花税
    stamp_tax = math.ceil(total_amount * 0.001)
    ext_fee += stamp_tax
    ext_detail["印花税"] = stamp_tax
    # 交易费
    transaction_fee = math.ceil(total_amount * 100 * 0.0000565) / 100.0
    ext_fee += transaction_fee
    ext_detail["交易费"] = transaction_fee
    # 证券会征费
    sec_fee = math.ceil(total_amount * 100 * 0.000027) / 100.0
    ext_fee += sec_fee
    ext_detail["证券会征费"] = sec_fee
    # 财汇局征费
    finance_fee = math.ceil(total_amount * 100 * 0.0000015) / 100.0
    ext_fee += finance_fee
    ext_detail["财汇局征费"] = finance_fee
    return ext_fee, ext_detail
