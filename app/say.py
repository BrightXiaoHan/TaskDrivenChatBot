from app.base import _BaseHandler
from backend import session_create, session_reply

__all__ = ["CreateSessionHandler", "ReplySessionHandler"]


class CreateSessionHandler(_BaseHandler):

    def _get_result_dict(self, **kwargs):
        return session_create(**kwargs)


class ReplySessionHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        return session_reply(**kwargs)
