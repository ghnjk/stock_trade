#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: futu_sdk
@author: jkguo
@create: 2024/10/19
"""
import pandas
import pandas as pd
from futu import OpenQuoteContext, KLType, RET_OK, TrdMarket, TrdEnv
import logging


class FutuSdk:

    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.logger = logging.getLogger("futu_sdk")

    def query_kline(self, stock_code: str, begin_time: str, end_time: str, k_line_type: str) -> pd.DataFrame:
        """
        查询k线
        :param stock_code:
        :param begin_time:
        :param end_time:
        :param k_line_type:
        :return:
        """
        begin_date = begin_time[:10]
        end_date = end_time[:10]
        self.logger.info(f"start query_kline {stock_code} {begin_date} to {end_date}")
        quote_ctx = OpenQuoteContext(host=self.host, port=self.port)  # 创建行情对象
        ret, data, page_req_key = quote_ctx.request_history_kline(code=stock_code, start=begin_date, end=end_date,
                                                                  ktype=k_line_type)
        df_list = [data]
        if ret != RET_OK:
            self.logger.error(f"query_kline {stock_code} {begin_date} to {end_date} failed: {data}")
            raise Exception(
                f"query_kline {stock_code} {begin_date} to {end_date} failed: {data}"
            )
        while page_req_key is not None:  # 请求后面的所有结果
            ret, data, page_req_key = quote_ctx.request_history_kline(code=stock_code, start=begin_date, end=end_date,
                                                                      ktype=k_line_type,
                                                                      max_count=100,
                                                                      page_req_key=page_req_key)  # 请求翻页后的数据
            if ret == RET_OK:
                df_list.append(data)
            else:
                self.logger.error(f"query_kline {stock_code} {begin_date} to {end_date} failed: {data}")
                raise Exception(
                    f"query_kline {stock_code} {begin_date} to {end_date} failed: {data}"
                )
        quote_ctx.close()  # 关闭对象，防止连接条数用尽
        df = pd.concat(df_list, ignore_index=True)
        return df[(df['time_key'] >= begin_time) & (df['time_key'] <= end_time)]
