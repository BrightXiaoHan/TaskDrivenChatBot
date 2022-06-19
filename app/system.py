from app.base import _BaseHandler
from backend import cluster, delete, push, delete_graph

__all__ = ["PushHandler", "DeleteHandler", "ClusterHandler", "DeleteGraphHandler"]


class PushHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        version = kwargs["version"]
        return await push(robot_code, version)


class DeleteHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return delete(robot_code)


class DeleteGraphHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        graph_id = kwargs["graph_id"]
        return delete_graph(robot_code, graph_id)


class ClusterHandler(_BaseHandler):
    async def _get_result_dict(self, **kwargs):
        robot_code = kwargs["robot_id"]
        return cluster(robot_code)
