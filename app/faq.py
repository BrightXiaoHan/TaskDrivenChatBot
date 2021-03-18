"""
FAQ引擎对外借口服务
"""
from backend import faq
from app.base import _BaseHandler

__all__ = ["FaqHandler"]


class FaqHandler(_BaseHandler):
    def _get_result_dict(self, **kwargs):
        robot_id = kwargs.get("robot_id")
        method = kwargs.get("method")
        data = kwargs.get("data", {})
        func = getattr(self, "_handle_" + method)
        return func(robot_id, data)

    def _handle_add(self, robot_id, data):
        return faq.faq_update(robot_id, data)

    def _handle_update(self, robot_id, data):
        return self._handle_add(robot_id, data)

    def _handle_delete(self, robot_id, data):
        return faq.faq_delete(robot_id, data)

    def _handle_ask(self, robot_id, data):
        return faq.faq_ask(robot_id, data["question"])