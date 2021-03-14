"""
服务启动入口
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler

import tornado
import app
from config import global_config

# 加载所需要的配置
LOG_DIR = global_config["logdir"]
SERVE_PORT = global_config["serve_port"]


def config_logging():
    """
    配置服务日志
    """
    log_fmt = '%(asctime)s\tFile\"%(filename)s\",line%(lineno)s\t%(levelname)s:%(message)s'
    formatter = logging.Formatter(log_fmt)
    # S 秒，D 天， M 分钟， H 小时，下面代表每间隔一天生成一个日志文件，每10天定时删除，日志文件存放在log目录下
    log_file_handler = TimedRotatingFileHandler(filename=os.path.join(LOG_DIR, "ServerLog"),
                                                when="D",
                                                interval=1,
                                                backupCount=10)
    log_file_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.addHandler(log_file_handler)


def main():
    """
    服务启动入口函数
    """
    config_logging()
    # 对服务的配置问题
    application = tornado.web.Application(
        [(r'/robot_manager/multi/train', app.TrainUpdateHandler),
         (r'/robot_manager/multi/say', app.SayHandler),
         (r'/robot_manager/multi/reload_model', app.ReloadModelHandler)]
    )
    http_server = tornado.httpserver.HTTPServer(application)
    # 2. 服务端口
    http_server.listen(SERVE_PORT)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
