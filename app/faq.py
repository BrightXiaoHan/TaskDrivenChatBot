"""FAQ引擎对外借口服务."""
from app.base import BaseHandler
from backend import faq
from utils.define import get_chitchat_faq_id
from utils.exceptions import MethodNotAllowException

__all__ = ["FaqHandler", "FaqChitchatHandler"]


class FaqHandler(BaseHandler):
    """处理FAQ相关请求."""

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
        delete_query = {"faq_ids": [item["faq_id"] for item in data]}
        await faq.faq_delete(robot_id, delete_query)
        return await self._handle_add(robot_id, data)

    async def _handle_delete(self, robot_id, data):
        return await faq.faq_delete(robot_id, data)

    async def _handle_ask(self, robot_id, data):
        return await faq.faq_ask(robot_id, data["question"])


class FaqChitchatHandler(FaqHandler):
    """处理基于FAQ的闲聊相关的请求."""

    async def _get_result_dict(self, **kwargs):
        # 将faqid进行包装，避免与正式对话产生冲突
        robot_id = kwargs.get("robot_id", "")
        robot_id = get_chitchat_faq_id(robot_id)
        kwargs.update({"robot_id": robot_id})
        return await super()._get_result_dict(**kwargs)

    async def _handle_add(self, robot_id, data):
        return await faq.faq_chitchat_update(robot_id, data)

    async def _handle_update(self, robot_id, data):
        delete_query = {"faq_ids": [item["chatfest_id"] for item in data]}
        await faq.faq_delete(robot_id, delete_query)
        return await self._handle_add(robot_id, data)

    async def _handle_ask(self, robot_id, data):
        return await faq.faq_chitchat_ask(robot_id, data["question"])

    async def _handle_delete(self, robot_id, data):
        ids = data.pop("chatfest_ids")
        data["faq_ids"] = ids
        return await faq.faq_delete(robot_id, data)
