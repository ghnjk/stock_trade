#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: stock_k_linke_lib
@author: jkguo
@create: 2024/10/18
"""
import typing
import datetime
import pandas as pd
import pytz
from jtrade.models.mysql_backend import StockKLineDto, StockKLineRepo, DtoUtil
from jtrade.core.futu_sdk import FutuSdk
from futu import KLType


class StockKLineLib(object):
    """
    股票K线数据lib
    """

    def __init__(self, stock_code: str,  repo: StockKLineRepo, futu_sdk: FutuSdk, time_unit: int = 1,
                 force_sync_from_futu: bool = False):
        self.stock_code = stock_code
        self.time_unit = time_unit
        self.repo = repo
        self.force_sync_from_futu = force_sync_from_futu
        self.timezone = pytz.timezone('Asia/Shanghai')
        self.df: typing.Optional[pd.DataFrame] = None
        self.df_min_query_time = None
        self.futu_sdk = futu_sdk

    def query(self, begin_time: str, end_time: str) -> pd.DataFrame:
        """
        需要优先从本地的df中查询，如果查询不到，再从外部同步
        :param begin_time:
        :param end_time:
        :return: pd.DataFrame
            列名： code,time_key,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close
        """
        begin_time = self._format_start_time_str(begin_time)
        end_time = self._format_end_time_str(end_time)
        if self.df_min_query_time is None or self.df is None or len(self.df) == 0 or begin_time < self.df_min_query_time:
            # 需要清空缓存，从投开始同步
            self.df = None
            need_sync_begin_time = begin_time
            need_sync_end_time = end_time
        else:
            df_end_time = self.df['time_key'].iloc[-1]
            if df_end_time >= end_time:
                # 无需同步数据
                need_sync_begin_time = None
                need_sync_end_time = None
            else:
                need_sync_begin_time = self._add_time(df_end_time, self.time_unit * 60)
                need_sync_end_time = end_time
        if need_sync_begin_time is not None and need_sync_end_time is not None:
            self._query(need_sync_begin_time, need_sync_end_time)
        if self.df_min_query_time is None or begin_time < self.df_min_query_time:
            self.df_min_query_time = begin_time
        return self.df[(self.df['time_key'] >= begin_time) & (self.df['time_key'] <= end_time)]

    def _query(self, begin_time: str | float, end_time: str | float) -> pd.DataFrame:
        if self.force_sync_from_futu:
            df = self._sync_kline_from_futu(begin_time, end_time)
        else:
            df = self._convert_list_to_df(self.repo.query(begin_time, end_time))
            need_sync_begin_time = begin_time
            if len(df) > 0:
                last_time_key = df['time_key'].iloc[-1]
                need_sync_begin_time = self._add_time(last_time_key, self.time_unit * 60)
            if need_sync_begin_time <= end_time:
                # 需要从外部同步数据
                sync_df = self._sync_kline_from_futu(need_sync_begin_time, end_time)
                # print(df.columns)
                # print(sync_df.columns)
                # print(df)
                # print(sync_df)
                if df is None or len(df) == 0:
                    df = sync_df
                else:
                    df = pd.concat([df, sync_df], ignore_index=True)
        if self.df is None:
            self.df = df
        else:
            # 合并两个 DataFrame
            merged_df = pd.concat([self.df, df], ignore_index=True)
            # 去除 time_key 列值相同的行
            merged_df = merged_df.drop_duplicates(subset='time_key', keep='last')
            # 重新设置索引和排序
            self.df = merged_df.sort_values(by='time_key').reset_index(drop=True)
        return df

    def _format_time_str(self, time_str: str | float):
        if isinstance(time_str, float):
            utc_time = datetime.datetime.utcfromtimestamp(time_str).replace(tzinfo=pytz.utc)
            local_time = utc_time.astimezone(self.timezone)
            formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            return formatted_time
        if len(time_str) == 19:
            return time_str
        if len(time_str) == 10:
            return time_str + ' 00:00:00'
        if len(time_str) == 13:
            return time_str + ':00:00'
        if len(time_str) == 16:
            return time_str + ':00'
        raise ValueError('time_str format error')

    def _format_start_time_str(self, time_str: str | float):
        if isinstance(time_str, float):
            utc_time = datetime.datetime.utcfromtimestamp(time_str).replace(tzinfo=pytz.utc)
            local_time = utc_time.astimezone(self.timezone)
            formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            return formatted_time
        if len(time_str) == 19:
            return time_str
        if len(time_str) == 10:
            return time_str + ' 09:30:00'
        if len(time_str) == 13:
            return time_str + ':30:00'
        if len(time_str) == 16:
            return time_str + ':00'
        raise ValueError('time_str format error')

    def _format_end_time_str(self, time_str: str | float):
        if isinstance(time_str, float):
            utc_time = datetime.datetime.utcfromtimestamp(time_str).replace(tzinfo=pytz.utc)
            local_time = utc_time.astimezone(self.timezone)
            formatted_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            return formatted_time
        if len(time_str) == 19:
            return time_str
        if len(time_str) == 10:
            return time_str + ' 16:00:00'
        if len(time_str) == 13:
            return time_str + ':00:00'
        if len(time_str) == 16:
            return time_str + ':00'
        raise ValueError('time_str format error')

    def _add_time(self, time_str: str, time_delta: int):
        time_str = self._format_time_str(time_str)
        local_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        local_time = self.timezone.localize(local_time)
        utc_time = local_time.astimezone(pytz.utc)
        timestamp = utc_time.timestamp()
        return self._format_time_str(timestamp + time_delta)

    def _sync_kline_from_futu(self, need_sync_begin_time: str, end_time: str) -> pd.DataFrame:
        res_df = self.futu_sdk.query_kline(self.stock_code, need_sync_begin_time, end_time, self._get_kline_type())
        res_df = res_df.drop(columns=['name'])
        # 需要将这些数据保存到数据库
        stock_dto_list = []
        for index, row in res_df.iterrows():
            row_dict = row.to_dict()
            row_dict["stock_code"] = row_dict["code"]
            row_dict["time_unit"] = self.time_unit
            stock_dto_list.append(DtoUtil.from_dict(StockKLineDto(), row_dict))
        self.repo.store(stock_dto_list)
        return res_df

    @staticmethod
    def _convert_list_to_df(k_list: typing.List[StockKLineDto]):
        """
        将k线列表转换为DataFrame
        列名： code,time_key,open,close,high,low,pe_ratio,turnover_rate,volume,turnover,change_rate,last_close
        :param k_list:
        :return:
        """
        columns = ['code', 'time_key', 'open', 'close', 'high', 'low', 'pe_ratio', 'turnover_rate', 'volume', 'turnover', 'change_rate', 'last_close']
        data = []
        for item in k_list:
            row = []
            for c in columns:
                if c == 'code':
                    c = 'stock_code'
                row.append(item.__getattribute__(c))
            data.append(row)
        return pd.DataFrame(data, columns=columns)

    def _get_kline_type(self):
        if self.time_unit == 1:
            return KLType.K_1M
        return KLType.NONE
