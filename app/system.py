from app.base import _BaseHandler
from backend import push, delete

__all__ = ["PushHandler", "DeleteHandler"]


class PushHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        return push(**kwargs)


class DeleteHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        return delete(**kwargs)
