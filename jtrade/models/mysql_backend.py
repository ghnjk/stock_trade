#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: mysql_backend
@author: jkguo
@create: 2024/10/17
"""
import logging
import typing
from datetime import datetime

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import text
import json
from jtrade.models.dto import DtoBase, DtoUtil, TradeAccountDto, TradeStockPropsDto, StockDto, TradeOrderDto, StockKLineDto

func_declarative_base = declarative_base
logger = logging.getLogger("mysql.backend")


class TradeAccountRepo(object):

    def __init__(self, trade_env: str, trade_market: str, session_maker):
        self.trade_env = trade_env
        self.trade_market = trade_market
        self.session_maker = session_maker

    def get(self, account_name: str) -> typing.Optional[TradeAccountDto]:
        session: Session = self.session_maker()
        try:
            db_dto = session.query(TradeAccountDto).filter(
                TradeAccountDto.trade_env == self.trade_env).filter(
                TradeAccountDto.trade_market == self.trade_market
            ).filter(
                TradeAccountDto.account_name == account_name).one()
            return db_dto
        except NoResultFound:
            return None
        except Exception as e:
            logger.error(f"TradeAccountRepo get {account_name} error: ", e)
            raise
        finally:
            session.close()

    def save(self, acc_dto: TradeAccountDto):
        session: Session = self.session_maker()
        try:
            session.merge(acc_dto)
            session.commit()
        except Exception as e:
            logger.error(f"TradeAccountRepo save {acc_dto.account_name} error: ", e)
            raise
        finally:
            session.close()


class StockRepo(object):

    def __init__(self, trade_env: str, trade_market: str, account_name: str, session_maker):
        self.trade_env = trade_env
        self.trade_market = trade_market
        self.account_name = account_name
        self.session_maker = session_maker

    def query_all(self, stock_code: str, stock_status_list: list[str] = None) -> typing.List[StockDto]:
        session: Session = self.session_maker()
        try:
            qry = session.query(StockDto).filter(
                StockDto.trade_env == self.trade_env).filter(
                StockDto.trade_market == self.trade_market).filter(
                StockDto.account_name == self.account_name).filter(
                StockDto.stock_code == stock_code
            )
            if stock_status_list is not None and len(stock_status_list) > 0:
                qry = qry.filter(StockDto.status.in_(stock_status_list))
            return qry.all()
        except NoResultFound:
            return []
        except Exception as e:
            logger.error(f"StockRepo query_all {stock_code} error: ", e)
            raise
        finally:
            session.close()

    def query_by_holding_id(self, stock_code: str, holding_id: str) -> typing.Optional[StockDto]:
        session: Session = self.session_maker()
        try:
            db_dto = session.query(StockDto).filter(
                StockDto.trade_env == self.trade_env).filter(
                StockDto.trade_market == self.trade_market).filter(
                StockDto.account_name == self.account_name).filter(
                StockDto.stock_code == stock_code).filter(
                StockDto.stock_holding_id == holding_id
            ).one()
            return db_dto
        except NoResultFound:
            return None
        except Exception as e:
            logger.error(f"StockRepo query_by_holding_id {stock_code} {holding_id} error: ", e)
            raise
        finally:
            session.close()

    def save(self, stock: StockDto):
        session: Session = self.session_maker()
        try:
            session.merge(stock)
            session.commit()
            logger.info(f"save stock {stock.stock_code} {stock.stock_holding_id} ok: {DtoUtil.to_dict(stock)}")
            return True
        except Exception as e:
            logger.error(f"StockRepo save {stock.stock_code} {stock.stock_holding_id} error: ", e)
            raise
        finally:
            session.close()


class TradeOrderRepo(object):

    def __init__(self, trade_env: str, trade_market: str, account_name: str, session_maker):
        self.trade_env = trade_env
        self.trade_market = trade_market
        self.account_name = account_name
        self.session_maker = session_maker

    def store(self, order: TradeOrderDto):
        session: Session = self.session_maker()
        try:
            session.merge(order)
            session.commit()
            logger.info(f"store order {order.order_id} ok: {DtoUtil.to_dict(order)}")
        except Exception as e:
            logger.error(f"StockOrderRepo store {order.order_id} error: ", e)
            raise
        finally:
            session.close()


class StockKLineRepo(object):

    def __init__(self, stock_code: str, time_unit: int, session_maker):
        self.stock_code = stock_code
        self.time_unit = time_unit
        self.session_maker = session_maker

    def query(self, begin_time: str, end_time: str) -> typing.List[StockKLineDto]:
        session: Session = self.session_maker()
        try:
            qry = session.query(StockKLineDto).filter(
                StockKLineDto.stock_code == self.stock_code).filter(
                StockKLineDto.time_unit == self.time_unit).filter(
                StockKLineDto.time_key >= begin_time).filter(
                StockKLineDto.time_key <= end_time
            ).order_by(StockKLineDto.time_key.asc())
            res = qry.all()
            logger.info(f"query stock kline ok. code {self.stock_code} unit {self.time_unit}"
                        f" {begin_time} to {end_time} count {len(res)}")
            return res
        except NoResultFound:
            logger.info(f"query stock kline ok. code {self.stock_code} unit {self.time_unit}"
                        f" {begin_time} to {end_time} count 0")
            return []
        except Exception as e:
            logger.error(f"StockKLineRepo query {begin_time} {end_time} error: ", e)
            raise
        finally:
            session.close()

    def store(self, stock_kline_list: typing.List[StockKLineDto]):
        session: Session = self.session_maker()
        try:
            for stock_kline in stock_kline_list:
                if stock_kline.stock_code != self.stock_code:
                    raise Exception("stock code not match")
                if stock_kline.time_unit != self.time_unit:
                    raise Exception("time unit not match")
                session.merge(stock_kline)
            session.commit()
            logger.info(f"store stock kline ok. code {self.stock_code} unit {self.time_unit} count {len(stock_kline_list)}")
        except Exception as e:
            session.rollback()
            logger.error(f"store stock kline code {self.stock_code} unit {self.time_unit}"
                         f"  failed: {e}")
            raise
        finally:
            session.close()


class MysqlBackend(object):
    """
        状态后端接口
        """

    def __init__(self, trade_env: str, trade_market: str, host: str, port: int,
                 user: str, password: str, db_name: str = "j_stock_db", echo_stdout=True) -> None:
        """

        :param trade_env: 交易环境：真实 / 模拟
        :param trade_market: 交易市场
        :param host: mysql host
        :param port: mysql port
        :param user: mysql 用户
        :param password:  mysql 密码
        :param db_name: 数据库名，默认： fptool_db
        """
        self.trade_env = trade_env
        self.trade_market = trade_market
        port = int(port)

        self.db_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}?charset=utf8",
                                       echo=echo_stdout)
        self.check_db_engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}?charset=utf8",
                                             echo=echo_stdout)

        # self.check_db_engine.logger = logging.getLogger("sqlalchemy")
        self.db_name = db_name
        self.DBSession = sessionmaker(bind=self.db_engine)

    def init_backend(self):
        """
        初始化存储后端，例如创建库表等
        :return:
        """
        self.init_db()

    def init_db(self):
        # prepare database
        with self.check_db_engine.connect() as con:
            # Query for existing databases
            existing_databases = con.execute(text('SHOW DATABASES;'))
            # Results are a list of single item tuples, so unpack each tuple
            existing_databases = [d[0] for d in existing_databases]

            # Create database if not exists
            if self.db_name not in existing_databases:
                con.execute(text("CREATE DATABASE {0}".format(self.db_name)))
                logger.info("Created database {0}".format(self.db_engine))
        # init all tables
        DtoBase.metadata.create_all(self.db_engine)

    def trade_account_repo(self) -> TradeAccountRepo:
        return TradeAccountRepo(self.trade_env, self.trade_market, self.DBSession)

    def stock_repo(self, account_name: str):
        return StockRepo(self.trade_env, self.trade_market, account_name, self.DBSession)

    def stock_k_line_repo(self, stock_code: str, time_unit: int = 1):
        return StockKLineRepo(stock_code, time_unit, self.DBSession)

    def trade_order_repo(self, account_name: str):
        return TradeOrderRepo(self.trade_env, self.trade_market, account_name, self.DBSession)


def main():
    backend = MysqlBackend(
        "SIMULATE", "HK.SIM",
        "localhost", 3306, "jk_dev", "jk_dev"
    )
    # 创建库表
    backend.init_db()


if __name__ == '__main__':
    main()
