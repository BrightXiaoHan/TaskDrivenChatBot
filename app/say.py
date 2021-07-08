from tornado.concurrent import run_on_executor
from app.base import _BaseHandler
from backend import session_create, session_reply
from utils.define import FAQ_DEFAULT_PERSPECTIVE

__all__ = ["CreateSessionHandler", "ReplySessionHandler"]


class CreateSessionHandler(_BaseHandler):

    @run_on_executor
    def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robotId"]
        user_code = kwargs["userCode"]
        params = kwargs["params"]
        return session_create(robot_code, user_code, params)


class ReplySessionHandler(_BaseHandler):

    @run_on_executor
    def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robotId"]
        session_id = kwargs["sessionId"]
        user_says = kwargs["userSays"]
        user_code = kwargs.get("userCode", "")
        params = kwargs.get("params", {})
        recommend_num = kwargs.get("recommend_num", 5)
        perspective = kwargs.get("perspective", FAQ_DEFAULT_PERSPECTIVE)

        faq_params = {
            "recommend_num": recommend_num,
            "perspective": perspective
        }

        return session_reply(robot_code, session_id, user_says, user_code, params, faq_params)
