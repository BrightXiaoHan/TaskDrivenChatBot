"""
存放一些日志辅助函数
"""
import os
import logging

from config import global_config

# 加载所需要的配置
LOG_DIR = global_config["log_dir"]

__all__ = ["config_logging"]


def config_logging():
    """
    配置服务日志，每间隔一天生成一个日志文件，每10天定时删除，日志文件存放在LOG_DIR目录下
    """
    log_fmt = '%(asctime)s\tFile\"%(filename)s\",line%(lineno)s\t%(levelname)s:%(message)s'
    formatter = logging.Formatter(log_fmt)
    log_file_handler = logging.handlers.TimedRotatingFileHandler(filename=os.path.join(LOG_DIR, "ServerLog"),
                                                                 when="D",
                                                                 interval=1,
                                                                 backupCount=10)
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.addHandler(log_file_handler)
