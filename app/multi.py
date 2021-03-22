from app.base import _BaseHandler
from app.executor import send_train_task
from backend import push, graph_train, nlu_train

__all__ = ["NLUHandler", "GraphHandler", "PushHandler"]


class NLUHandler(_BaseHandler):

    def _get_result_dict(self, **kwargs):
        response_data = nlu_train(**kwargs)
        send_train_task(**kwargs)
        return response_data


class GraphHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        return graph_train(**kwargs)


class PushHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        return push(**kwargs)
