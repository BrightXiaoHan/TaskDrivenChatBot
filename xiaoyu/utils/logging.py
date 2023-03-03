"""
存放一些日志辅助函数
"""
import logging

import logstash


def get_logger(name: str, elk_host: str = "localhost", elk_port: int = 15044) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(logstash.LogstashHandler(elk_host, elk_port, version=1))
    return logger
