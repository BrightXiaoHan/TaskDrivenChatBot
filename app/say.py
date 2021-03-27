from app.base import _BaseHandler
from backend import session_create, session_reply

__all__ = ["CreateSessionHandler", "ReplySessionHandler"]


class CreateSessionHandler(_BaseHandler):

    def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robotId"]
        user_code = kwargs["userCode"]
        params = kwargs["params"]
        return session_create(robot_code, user_code, params)


class ReplySessionHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robotId"]
        session_id = kwargs["sessionId"]
        user_says = kwargs["userSays"]

        return session_reply(robot_code, session_id, user_says)
