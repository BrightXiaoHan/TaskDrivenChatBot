from app.base import BaseHandler
from backend import cluster, delete, delete_graph, push, sensitive_words

__all__ = [
    "PushHandler",
    "DeleteHandler",
    "ClusterHandler",
    "DeleteGraphHandler",
    "SensitiveWordsHandler",
]


class PushHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        version = kwargs["version"]
        return await push(robot_code, version)


class DeleteHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return delete(robot_code)


class DeleteGraphHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        graph_id = kwargs["graph_id"]
        return delete_graph(robot_code, graph_id)


class ClusterHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return cluster(robot_code)


class SensitiveWordsHandler(BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        text = kwargs["text"]
        labels = kwargs["labels"]
        strict = kwargs["strict"]
        # TODO
        strict = False
        return await sensitive_words(robot_code, text, labels, strict)
