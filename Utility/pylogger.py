# -*- coding:utf-8 -*-

import logging
import global_variable


def setup_logger(cls_name):
    '''
    根据调用方的类名实例化日志引用。
     cls_name：类名。
    '''
    logger = logging.getLogger(cls_name)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(global_variable.file_folder + '.\\log.txt', 'a')
    file_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    return logger
