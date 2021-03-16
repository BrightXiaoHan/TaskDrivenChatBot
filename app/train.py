from .base import _BaseHandler
from .executor import send_train_task

__all__ = ["TrainHandler", "DeleteHandler", "PushHandler", "UdpateHandler"]


class TrainHandler(_BaseHandler):

    def _get_result_dict(self, **kwargs):
        send_train_task(**kwargs)
        return {"status_code": 0}


class DeleteHandler(_BaseHandler):
    pass


class PushHandler(_BaseHandler):
    pass


class UdpateHandler(_BaseHandler):
    pass
