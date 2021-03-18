"""
服务启动入口
"""
import tornado
import app
from config import global_config
from utils.logging import config_logging

SERVE_PORT = global_config["serve_port"]


def main():
    """
    服务启动入口函数
    """
    config_logging()
    app.fork_train_process()
    # 对服务的配置问题
    application = tornado.web.Application([
        (r'/xiaoyu/faq', app.FaqHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    # 2. 服务端口
    http_server.listen(SERVE_PORT)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
