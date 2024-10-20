#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: dto
@author: jkguo
@create: 2024/10/18
"""
from datetime import datetime
import sqlalchemy
from sqlalchemy import String, JSON, Integer, Float, DateTime, sql, Column, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped
DtoBase = sqlalchemy.orm.declarative_base()


class DtoUtil(object):

    @classmethod
    def to_dict(cls, o: any) -> dict:
        doc = {}
        for c in o.columns:
            try:
                v = o.__getattribute__(c)
                if isinstance(v, datetime):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                doc[c] = v
            except Exception as ignoredE:
                pass
        return doc

    @classmethod
    def from_dict(cls, o: any, doc: dict):
        for c in o.columns:
            o.__setattr__(c, doc.get(c))
        return o

    @classmethod
    def copy(cls, src: any, dst: any):
        DtoUtil.from_dict(dst, DtoUtil.to_dict(src))


class TradeAccountDto(DtoBase):
    """
    股票账户信息表
    """
    __tablename__ = "t_trade_account"
    __table_args__ = (PrimaryKeyConstraint(
        "trade_env", "trade_market", "account_name"
    ), {
                          "mysql_default_charset": "utf8"
                      })
    trade_env: Mapped[str] = Column('trade_env', String(16),  comment='交易环境：真实 / 模拟')
    trade_market: Mapped[str] = Column('trade_market', String(32),  comment='交易市场')
    account_name: Mapped[str] = Column('account_name', String(128), comment='账户名称')
    trade_pwd: Mapped[str] = Column('trade_pwd', String(256), comment='交易密码')
    modify_user: Mapped[str] = Column('modify_user', String(128), default="", server_default="",
                                      comment="修改用户")
    account_balance: Mapped[float] = Column('account_balance', Float, default=0, server_default="0",
                                            comment='账户余额')
    create_time: Mapped[datetime] = Column('create_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='创建时间')
    modify_time: Mapped[datetime] = Column('modify_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='修改时间')
    columns = [
        "trade_env", "trade_market", "account_name", "trade_pwd",
        "modify_user", "account_balance", "create_time", "modify_time"
    ]


class TradeStockPropsDto(DtoBase):
    """
    股票交易属性表
    """
    __tablename__ = "t_trade_stock_props"
    __table_args__ = (PrimaryKeyConstraint(
        "trade_env", "trade_market", "account_name", "stock_code"
    ), {
                          "mysql_default_charset": "utf8"
                      })
    trade_env: Mapped[str] = Column('trade_env', String(16),  comment='交易环境：真实 / 模拟')
    trade_market: Mapped[str] = Column('trade_market', String(32),  comment='交易市场')
    account_name: Mapped[str] = Column('account_name', String(128), comment='账户名称')
    stock_code: Mapped[str] = Column('stock_code', String(128), comment='股票代码')
    max_position: Mapped[int] = Column('max_position', Float, comment='最大持仓数')
    trade_alg_params: Mapped[dict] = Column('trade_alg_params', JSON, comment='交易算法参数')
    modify_user: Mapped[str] = Column('modify_user', String(128), default="", server_default="",
                                      comment="修改用户")
    create_time: Mapped[datetime] = Column('create_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='创建时间')
    modify_time: Mapped[datetime] = Column('modify_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='修改时间')
    columns = [
        "trade_env", "trade_market", "account_name", "stock_code", "max_position",
        "trade_alg_params",
        "modify_user", "create_time", "modify_time"
    ]


class StockStatus(object):

    INIT = 0
    BUYING = 1
    HOLDING = 2
    SELLING = 3
    SOLD = 4
    DELETED = 5


class StockDto(DtoBase):
    """
    持有股票信息表
    """
    __tablename__ = "t_stock"
    __table_args__ = (PrimaryKeyConstraint(
        "trade_env", "trade_market", "account_name", "stock_code", "stock_holding_id"
    ), {
                          "mysql_default_charset": "utf8"
                      })
    trade_env: Mapped[str] = Column('trade_env', String(16), comment='交易环境：真实 / 模拟')
    trade_market: Mapped[str] = Column('trade_market', String(32), comment='交易市场')
    account_name: Mapped[str] = Column('account_name', String(128), comment='账户名称')
    stock_code: Mapped[str] = Column('stock_code', String(128), comment='股票代码')
    stock_holding_id: Mapped[str] = Column('stock_holding_id', String(64), comment='股票持有id')
    status: Mapped[int] = Column('status', Integer, comment='状态：0: 初始化，1: 买入中， 2：持有中, 3:  卖出中, 4: 已卖出, 5: 已删除')
    quantity: Mapped[int] = Column('quantity', Integer, comment='持有数量')
    buy_price: Mapped[float] = Column('buy_price', Float, comment='买入单价')
    buy_total_amount: Mapped[float] = Column('buy_total_amount', Float, comment='买入总金额')
    buy_all_ext_fee: Mapped[float] = Column('buy_all_ext_fee', Float, comment='买入缴纳的其他费用')
    buy_order_id: Mapped[str] = Column('buy_order_id', String(64), comment='买入订单id')
    buy_time: Mapped[str] = Column('buy_time', String(32), comment='买入的交易时间 yyyy-mm-dd HH:MM:ss')
    sell_price: Mapped[float] = Column('sell_price', Float, comment='卖出单价')
    sell_total_amount: Mapped[float] = Column('sell_total_amount', Float, comment='卖出总金额')
    sell_all_ext_fee: Mapped[float] = Column('sell_all_ext_fee', Float, comment='卖出缴纳的其他费用')
    sell_order_id: Mapped[str] = Column('sell_order_id', String(64), comment='卖出订单id')
    sell_time: Mapped[str] = Column('sell_time', String(32), comment='卖出的交易时间 yyyy-mm-dd HH:MM:ss')
    trade_profit: Mapped[float] = Column('trade_profit', Float, comment='交易盈亏')
    create_time: Mapped[datetime] = Column('create_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='创建时间')
    modify_time: Mapped[datetime] = Column('modify_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='修改时间')
    columns = [
        "trade_env", "trade_market", "account_name", "stock_code", "stock_holding_id",
        "status", "quantity", "buy_price", "buy_total_amount", "buy_all_ext_fee", "buy_order_id", "buy_time"
        "sell_price", "sell_total_amount", "sell_all_ext_fee", "sell_order_id", "sell_time", "trade_profit",
        "create_time", "modify_time"
    ]


class TradeOrderStatus(object):
    """
    订单状态： 0 初始化, 1: 未成交 / 2: 部分成交 / 3: 全部成交 / 4: 已撤单 / 5: 已删除
    """

    INITIALIZED = 0
    TRADING = 1
    PART_TRADED = 2
    ALL_TRADED = 3
    CANCELLED = 4
    DELETED = 5


class TradeOrderDto(DtoBase):
    """
    股票交易订单表
    """
    __tablename__ = "t_trade_order"
    __table_args__ = (PrimaryKeyConstraint(
        "trade_env", "trade_market", "account_name", "order_id"
    ), {
                          "mysql_default_charset": "utf8"
                      })
    trade_env: Mapped[str] = Column('trade_env', String(16), comment='交易环境：真实 / 模拟')
    trade_market: Mapped[str] = Column('trade_market', String(32), comment='交易市场')
    account_name: Mapped[str] = Column('account_name', String(128), comment='账户名称')
    order_id: Mapped[str] = Column('order_id', String(64), comment='订单id')
    trade_side: Mapped[str] = Column('trade_side', String(16), comment='订单类型：TrdSide.BUY / TrdSide.SELL')
    order_status: Mapped[int] = Column('order_status', Integer, comment='订单状态： 0 初始化, , 1: 未成交 / 2: 部分成交 / 3: 全部成交 / 4: 已撤单 / 5: 已删除')
    stock_code: Mapped[str] = Column('stock_code', String(128), index=True, comment='股票代码')
    stock_holding_id: Mapped[str] = Column('stock_holding_id', String(64), comment='股票持有id')
    quantity: Mapped[int] = Column('quantity', Integer, comment='数量')
    price: Mapped[float] = Column('price', Float, comment='单价')
    total_amount: Mapped[float] = Column('total_amount', Float, comment='总金额')
    ext_fee: Mapped[float] = Column('ext_fee', Float, comment='其他费用')
    ext_fee_detail: Mapped[dict] = Column('ext_fee_detail', JSON, comment='其他费用明细')
    submit_time: Mapped[datetime] = Column('submit_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='提交时间')
    complete_time: Mapped[str] = Column('complete_time', String(32), index=True, comment='完成时间 yyyy-mm-dd HH:MM:SS ')
    cancel_time: Mapped[datetime] = Column('cancel_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='撤单时间')
    valid_time: Mapped[datetime] = Column('valid_time', DateTime, index=True, default=datetime.now(),
                                          server_default=sql.func.now(), comment='有效时间')
    trader: Mapped[str] = Column('trader', String(128), comment='交易员')
    notes: Mapped[str] = Column('notes', String(128), comment='备注')
    ext_detail: Mapped[dict] = Column('ext_detail', JSON, comment='其他信息')
    create_time: Mapped[datetime] = Column('create_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='创建时间')
    modify_time: Mapped[datetime] = Column('modify_time', DateTime, index=True, default=datetime.now(),
                                           server_default=sql.func.now(), comment='修改时间')
    columns = [
        "trade_env", "trade_market", "account_name", "order_id", "order_type", "order_status", "stock_code",
        "stock_holding_id", "quantity", "price", "ext_fee", "ext_fee_detail", "submit_time", "complete_time",
        "cancel_time", "valid_time", "trader", "notes", "ext_detail", "create_time", "modify_time"
    ]


class StockKLineDto(DtoBase):
    """
    股票K线数据
    time_key, time_unit,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close
    """
    __tablename__ = "t_stock_k_line"
    __table_args__ = (PrimaryKeyConstraint(
        "time_key", "stock_code", "time_unit"
    ), {
                          "mysql_default_charset": "utf8"
                      })
    time_key: Mapped[str] = Column('time_key', String(20), comment='事件yyyy-mm-dd HH:MM:SS')
    stock_code: Mapped[str] = Column('stock_code', String(128), comment='股票代码')
    time_unit: Mapped[int] = Column('time_unit', Integer, comment='时间单位 min')
    open: Mapped[float] = Column('open', Float, comment='开盘价')
    close: Mapped[float] = Column('close', Float, comment='收盘价')
    high: Mapped[float] = Column('high', Float, comment='最高价')
    low: Mapped[float] = Column('low', Float, comment='最低价')
    pe_ratio: Mapped[float] = Column('pe_ratio', Float, comment='市盈率')
    turnover_rate: Mapped[float] = Column('turnover_rate', Float, comment='换手率')
    volume: Mapped[float] = Column('volume', Float, comment='成交量')
    turnover: Mapped[float] = Column('turnover', Float, comment='成交额')
    change_rate: Mapped[float] = Column('change_rate', Float, comment='涨跌幅')
    last_close: Mapped[float] = Column('last_close', Float, comment='昨收价')
    columns = [
        "time_key", "stock_code", "time_unit", "open", "close", "high", "low", "pe_ratio", "turnover_rate", "volume",
        "turnover", "change_rate", "last_close"
    ]
