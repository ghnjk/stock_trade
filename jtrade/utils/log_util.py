#!/usr/bin/env python3
# -*- coding:utf-8 _*-
"""
@file: log_util
@author: jkguo
@create: 2024/10/19
"""
import logging
import json
import sys
import traceback
from logging.handlers import RotatingFileHandler


def clear_logger_handlers(logger):
    if logger is not None:
        for handler in logger.handlers:
            logger.removeHandler(handler)


def set_stdout_logger(
        log_level=logging.DEBUG,
        logger=None,
):
    if logger is None:
        logger = logging.getLogger()
    elif isinstance(logger, str):
        logger = logging.getLogger(logger)
    logger.setLevel(log_level)
    clear_logger_handlers(logger)
    formatter = logging.Formatter(
        "[%(asctime)s %(msecs)03d][%(process)d][tid=%(thread)d][%(name)s][%(levelname)s] %(message)s [%(filename)s"
        " %(funcName)s %(lineno)s] ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def set_file_logger(
        log_file_path,
        log_level=logging.DEBUG,
        max_file_size_mb=100,
        max_file_count=20,
        encoding="UTF-8",
        logger=None,
):
    """
    (重新)设定设定日志文件
    """
    if logger is None:
        logger = logging.getLogger()
    elif isinstance(logger, str):
        logger = logging.getLogger(logger)
    logger.setLevel(log_level)
    clear_logger_handlers(logger)
    formatter = logging.Formatter(
        "[%(asctime)s %(msecs)03d][%(process)d][tid=%(thread)d][%(name)s][%(levelname)s] %(message)s [%(filename)s"
        " %(funcName)s %(lineno)s] ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=max_file_count,
        encoding=encoding,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

