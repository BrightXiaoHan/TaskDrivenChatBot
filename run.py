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
    application = tornado.web.Application([
        (r'/xiaoyu/faq', app.FaqHandler),
        (r'/xiaoyu/multi/nlu', app.NLUHandler),
        (r'/xiaoyu/multi/graph', app.GraphHandler),
        (r'/xiaoyu/push', app.PushHandler),
        (r'/xiaoyu/delete', app.DeleteHandler),
        (r'/api/v1/session/create', app.CreateSessionHandler),
        (r'/api/v1/session/reply', app.ReplySessionHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(SERVE_PORT)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
