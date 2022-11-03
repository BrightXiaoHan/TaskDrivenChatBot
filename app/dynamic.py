from app.base import BaseHandler
from backend import (
    dynamic_intent_delete,
    dynamic_intent_train,
    dynamic_qa_delete,
    dynamic_qa_train,
)

__all__ = ["DynamicIntentTrainHandler", "DynamicQATrainHandler"]


class DynamicIntentTrainHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        method = kwargs["method"]
        data = kwargs["data"]
        if method == "update":
            return await dynamic_intent_train(data)
        elif method == "delete":
            return await dynamic_intent_delete(data)
        else:
            raise AttributeError("method must be train or delete")


class DynamicQATrainHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        method = kwargs["method"]
        data = kwargs["data"]
        if method == "update":
            return await dynamic_qa_train(data)
        elif method == "delete":
            return await dynamic_qa_delete(data)
        else:
            raise AttributeError("method must be update or delete")
