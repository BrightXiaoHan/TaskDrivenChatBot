import backend as bk
from app.base import _BaseHandler
from app.executor import send_train_task

__all__ = ["NLUHandler", "GraphHandler", "PushHandler"]


class NLUHandler(_BaseHandler):

    def _get_result_dict(self, **kwargs):
        send_train_task(**kwargs)
        return {"status_code": 0}


class GraphHandler(_BaseHandler):
    pass


class PushHandler(_BaseHandler):
    pass
