"""
FAQ引擎对外借口服务
"""
from backend import faq
from app.base import _BaseHandler
from utils.exceptions import MethodNotAllowException

__all__ = ["FaqHandler"]


class FaqHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_id = kwargs.get("robot_id")
        method = kwargs.get("method")
        data = kwargs.get("data", {})
        allowed_methods = ["add", "update", "delete", "ask"]
        if method not in allowed_methods:
            raise MethodNotAllowException(method, allowed_methods)

        func = getattr(self, "_handle_" + method)
        return await func(robot_id, data)

    async def _handle_add(self, robot_id, data):
        return await faq.faq_update(robot_id, data)

    async def _handle_update(self, robot_id, data):
        delete_query = {
            "faq_ids": [item["faq_id"] for item in data]
        }
        await faq.faq_delete(robot_id, delete_query)
        return await self._handle_add(robot_id, data)

    async def _handle_delete(self, robot_id, data):
        return await faq.faq_delete(robot_id, data)

    async def _handle_ask(self, robot_id, data):
        return await faq.faq_ask(robot_id, data["question"])
