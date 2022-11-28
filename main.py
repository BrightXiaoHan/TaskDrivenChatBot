"""服务启动入口."""
import tornado

import app
from config import global_config
from utils.logging import config_logging

SERVE_PORT = global_config["serve_port"]


def main():
    """服务启动入口函数."""
    config_logging()
    app.fork_train_process()
    application = tornado.web.Application(
        [
            (r"/xiaoyu/faq", app.FaqHandler),
            (r"/xiaoyu/faq/chitchat", app.FaqChitchatHandler),
            (r"/xiaoyu/multi/nlu", app.NLUTrainHandler),
            (r"/xiaoyu/multi/graph", app.GraphHandler),
            (r"/xiaoyu/push", app.PushHandler),
            (r"/xiaoyu/delete", app.DeleteHandler),
            (r"/xiaoyu/delete/graph", app.DeleteGraphHandler),
            (r"/api/v1/session/reply", app.ReplySessionHandler),
            (r"/xiaoyu/analyze", app.NLUHandler),
            (r"/xiaoyu/cluster", app.ClusterHandler),
            (r"/xiaoyu/sensitive_words", app.SensitiveWordsHandler),
            (r"/xiaoyu/sensitive_words/train", app.SensitiveWordsTrainHandler),
            (r"/xiaoyu/multi/qadb", app.DynamicQATrainHandler),
            (r"/xiaoyu/multi/intentdb", app.DynamicIntentTrainHandler),
        ]
    )
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(SERVE_PORT)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
